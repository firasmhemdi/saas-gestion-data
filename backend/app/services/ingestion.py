import csv
import io
import json
import re
import time
import zipfile
from datetime import date, datetime, timezone
from typing import Any

from app.models.ingestion import DocumentType


def parse_tabular_content(filename: str, content: str, delimiter: str | None = None) -> tuple[list[str], list[dict[str, Any]]]:
    if filename.lower().endswith(".xlsx"):
        return _parse_xlsx(content)

    sample = content[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[delimiter, ",", ";", "\t"] if delimiter else [",", ";", "\t"])
    except csv.Error:
        dialect = csv.excel
        if delimiter:
            dialect.delimiter = delimiter
        elif ";" in sample and sample.count(";") >= sample.count(","):
            dialect.delimiter = ";"
    reader = csv.DictReader(io.StringIO(content), dialect=dialect)
    rows = [{k: _clean_cell(v) for k, v in row.items()} for row in reader]
    return list(reader.fieldnames or []), rows


def _parse_xlsx(content: str) -> tuple[list[str], list[dict[str, Any]]]:
    import base64
    import xml.etree.ElementTree as ET

    data = base64.b64decode(content)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall(".//x:si", ns):
                shared.append("".join(t.text or "" for t in item.findall(".//x:t", ns)))
        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        matrix: list[list[str]] = []
        for row in sheet.findall(".//x:row", ns):
            values: list[str] = []
            for cell in row.findall("x:c", ns):
                value = cell.find("x:v", ns)
                raw = value.text if value is not None else ""
                if cell.attrib.get("t") == "s" and raw:
                    raw = shared[int(raw)]
                values.append(raw)
            matrix.append(values)
    if not matrix:
        return [], []
    headers = [str(h).strip() for h in matrix[0]]
    rows = [dict(zip(headers, row, strict=False)) for row in matrix[1:]]
    return headers, rows


def suggest_mapping(columns: list[str]) -> dict[str, str]:
    suggestions: dict[str, str] = {}
    aliases = {
        "entry_date": ("date", "jour", "invoice_date", "document_date", "periode", "period"),
        "value": ("value", "valeur", "quantity", "quantite", "product_qty", "montant", "amount"),
        "unit": ("unit", "unite", "uom"),
    }
    lowered = {c.lower().replace("é", "e").replace("è", "e"): c for c in columns}
    for target, keys in aliases.items():
        for key in keys:
            found = next((original for normalized, original in lowered.items() if key in normalized), None)
            if found:
                suggestions[target] = found
                break
    return suggestions


def commit_rows(rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        entry_date = _parse_date(row.get(mapping.get("entry_date", "")))
        value = _parse_float(row.get(mapping.get("value", "")))
        unit = str(row.get(mapping.get("unit", ""), "") or "").strip()
        if not entry_date or value is None or not unit:
            continue
        output.append({"entry_date": entry_date, "value": value, "unit": unit})
    return output


def classify_document(text: str, filename: str = "") -> DocumentType:
    haystack = f"{filename}\n{text}".lower()
    if any(k in haystack for k in ("facture", "electricite", "électricité", "gaz", "kwh")):
        return DocumentType.facture_energie
    if any(k in haystack for k in ("bordereau", "dechet", "déchet", "benne", "tonne")):
        return DocumentType.bordereau_dechets
    if "contrat" in haystack:
        return DocumentType.contrat
    if any(k in haystack for k in ("attestation", "certificat")):
        return DocumentType.attestation
    return DocumentType.autre


def extract_document_fields(text: str) -> tuple[dict[str, Any], int]:
    normalized = " ".join(text.split())
    searchable = _normalize_for_search(normalized)
    fields: dict[str, Any] = {}
    is_steg_bill = any(keyword in searchable for keyword in ("steg", "societe tunisienne", "electricite et du gaz", "montant a payer"))

    dates = re.findall(r"(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", normalized)
    if dates:
        parsed = _parse_date(dates[0])
        if parsed:
            fields["document_date"] = parsed.isoformat()
    parsed_dates = [parsed for raw in dates if (parsed := _parse_date(raw))]
    period = _extract_period(parsed_dates, prefer_earliest=is_steg_bill)
    if period:
        fields["period_start"] = period[0].isoformat()
        fields["period_end"] = period[1].isoformat()

    if is_steg_bill:
        fields["provider"] = "STEG"

    amount_due = _extract_amount_due(normalized)
    if amount_due is not None:
        fields["amount_due"] = amount_due

    amount = _extract_total_amount(normalized)
    if amount is not None:
        fields["amount"] = amount

    if is_steg_bill and "index" in searchable:
        consumption_values = _extract_consumption_from_indexes(normalized)
        if consumption_values:
            fields["quantity"] = consumption_values[0]
            fields["unit"] = "kWh"
        if len(consumption_values) > 1:
            fields["gas_quantity"] = consumption_values[1]
            fields["gas_unit"] = "m3"

    quantity_match = re.search(r"([0-9]+(?:[,.][0-9]+)?)\s*(kwh|m3|m³|t|tonnes?|litres?|l)\b", normalized, re.IGNORECASE)
    if quantity_match and "quantity" not in fields:
        fields["quantity"] = _parse_float(quantity_match.group(1))
        fields["unit"] = quantity_match.group(2)
    elif "quantity" not in fields and any(keyword in searchable for keyword in ("electricite", "eclairage", "kwh")):
        electricity_quantity = _extract_after_keywords(normalized, ("electricite", "électricité", "eclairage", "éclairage"), window=140)
        if electricity_quantity is not None and electricity_quantity >= 20:
            fields["quantity"] = electricity_quantity
            fields["unit"] = "kWh"

    gas_match = re.search(r"([0-9]+(?:[,.][0-9]+)?)\s*(m3|m³)\b", normalized, re.IGNORECASE)
    if gas_match and "gas_quantity" not in fields:
        fields["gas_quantity"] = _parse_float(gas_match.group(1))
        fields["gas_unit"] = gas_match.group(2)
    elif "gas_quantity" not in fields and "gaz" in searchable:
        gas_quantity = _extract_after_keywords(normalized, ("gaz",), window=140)
        if gas_quantity is not None and gas_quantity >= 5 and gas_quantity != fields.get("quantity"):
            fields["gas_quantity"] = gas_quantity
            fields["gas_unit"] = "m3"

    supplier_match = re.search(r"(?:fournisseur|supplier)\s*[:=]\s*([A-Za-z0-9 &.'-]{2,80})", normalized, re.IGNORECASE)
    if supplier_match:
        fields["provider"] = supplier_match.group(1).strip()

    confidence = _estimate_extraction_confidence(fields, is_steg_bill)
    return fields, confidence


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _clean_cell(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return None


def _normalize_for_search(value: str) -> str:
    replacements = str.maketrans({"é": "e", "è": "e", "ê": "e", "à": "a", "â": "a", "ù": "u", "ç": "c", "ï": "i", "î": "i"})
    return value.lower().translate(replacements)


def _extract_total_amount(text: str) -> float | None:
    label_match = re.search(r"(?:montant\s+total|total\s+ttc|total\s+consommation\s*&\s*services)(.{0,45})", text, re.IGNORECASE)
    if label_match:
        parsed = _last_amount_in_text(label_match.group(1), min_value=10)
        if parsed is not None:
            return parsed

    direct_match = re.search(r"(?:montant|total|ttc)\s*[:=]?\s*([0-9]+(?:[,.][0-9]+)?)", text, re.IGNORECASE)
    if direct_match:
        parsed = _parse_float(direct_match.group(1))
        if parsed is not None and parsed != 16:
            return parsed
    return None


def _extract_amount_due(text: str) -> float | None:
    label_match = re.search(r"(?:montant\s+(?:a|à)\s+payer)(.{0,100})", text, re.IGNORECASE)
    if label_match:
        parsed = _last_amount_in_text(label_match.group(1), min_value=50)
        if parsed is not None:
            return parsed
    before_label_match = re.search(r"(.{0,100})(?:montant\s+(?:a|à)\s+payer)", text, re.IGNORECASE)
    if before_label_match:
        parsed = _last_amount_in_text(before_label_match.group(1), min_value=50)
        if parsed is not None:
            return parsed

    patterns = (
        r"(?:montant\s+(?:a|à)\s+payer)\D{0,80}([0-9]+(?:[,.][0-9]+)?)",
        r"([0-9]+(?:[,.][0-9]+)?)\D{0,80}(?:montant\s+(?:a|à)\s+payer)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            parsed = _parse_float(match.group(1))
            if parsed is not None and parsed >= 50:
                return parsed

    amounts = _amount_candidates(text, min_value=50)
    return max(amounts) if amounts else None


def _last_amount_in_text(text: str, min_value: float = 0) -> float | None:
    amounts = _amount_candidates(text, min_value=min_value)
    return amounts[-1] if amounts else None


def _amount_candidates(text: str, min_value: float = 0) -> list[float]:
    amounts: list[float] = []
    for raw in re.findall(r"\b([0-9]+[,.][0-9]{2,3})\b", text):
        parsed = _parse_float(raw)
        if parsed is not None and min_value <= parsed <= 100000:
            amounts.append(parsed)
    return amounts


def _extract_period(parsed_dates: list[date], prefer_earliest: bool = False) -> tuple[date, date] | None:
    if len(parsed_dates) < 2:
        return None
    if prefer_earliest:
        ordered = sorted(set(parsed_dates))
        if len(ordered) >= 2:
            return ordered[0], ordered[1]
    for index, first_period in enumerate(parsed_dates):
        second_period = next((candidate for candidate in parsed_dates[index + 1 :] if first_period < candidate), None)
        if second_period:
            return first_period, second_period
    return None


def _extract_consumption_from_indexes(text: str) -> list[float]:
    values: list[float] = []
    integer_tokens = [int(match.group(1)) for match in re.finditer(r"\b([0-9]{4,6})\b", text)]
    for previous, current in zip(integer_tokens, integer_tokens[1:], strict=False):
        difference = previous - current
        if 5 <= difference <= 50000 and difference not in values:
            values.append(float(difference))
    return values[:2]


def _extract_after_keywords(text: str, keywords: tuple[str, ...], window: int = 120) -> float | None:
    normalized = _normalize_for_search(text)
    normalized_keywords = tuple(_normalize_for_search(keyword) for keyword in keywords)
    for keyword in normalized_keywords:
        index = normalized.find(keyword)
        if index == -1:
            continue
        snippet = text[index : index + window]
        numbers = re.findall(r"\b([0-9]+(?:[,.][0-9]+)?)\b", snippet)
        for raw in numbers:
            parsed = _parse_float(raw)
            if parsed is not None and parsed > 0:
                return parsed
    return None


def _estimate_extraction_confidence(fields: dict[str, Any], is_steg_bill: bool) -> int:
    confidence = min(95, 45 + len(fields) * 10)
    if not is_steg_bill:
        return confidence

    suspicious = False
    amount_due = _parse_float(fields.get("amount_due"))
    amount = _parse_float(fields.get("amount"))
    quantity = _parse_float(fields.get("quantity"))
    gas_quantity = _parse_float(fields.get("gas_quantity"))

    if fields.get("provider") != "STEG":
        suspicious = True
    if amount_due is not None and amount_due < 50:
        suspicious = True
    if amount is not None and amount < 20:
        suspicious = True
    if quantity is not None and quantity < 20:
        suspicious = True
    if gas_quantity is not None and gas_quantity < 5:
        suspicious = True

    return min(confidence, 65) if suspicious else confidence


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None
