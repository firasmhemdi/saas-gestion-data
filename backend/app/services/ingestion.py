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
    fields: dict[str, Any] = {}

    date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", normalized)
    if date_match:
        parsed = _parse_date(date_match.group(1))
        if parsed:
            fields["document_date"] = parsed.isoformat()

    amount_match = re.search(r"(?:montant|total|ttc)\s*[:=]?\s*([0-9]+(?:[,.][0-9]+)?)", normalized, re.IGNORECASE)
    if amount_match:
        fields["amount"] = _parse_float(amount_match.group(1))

    quantity_match = re.search(r"([0-9]+(?:[,.][0-9]+)?)\s*(kwh|m3|m³|t|tonnes?|litres?|l)\b", normalized, re.IGNORECASE)
    if quantity_match:
        fields["quantity"] = _parse_float(quantity_match.group(1))
        fields["unit"] = quantity_match.group(2)

    supplier_match = re.search(r"(?:fournisseur|supplier)\s*[:=]\s*([A-Za-z0-9 &.'-]{2,80})", normalized, re.IGNORECASE)
    if supplier_match:
        fields["provider"] = supplier_match.group(1).strip()

    confidence = min(95, 45 + len(fields) * 12)
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
