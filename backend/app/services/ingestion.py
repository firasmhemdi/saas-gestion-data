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
    haystack = _normalize_for_search(f"{filename}\n{text}")
    if any(k in haystack for k in ("facture", "electricite", "gaz", "kwh", "khw", "kw h", "steg", "sonede", "releve")):
        return DocumentType.facture_energie
    if any(k in haystack for k in ("bordereau", "dechet", "benne", "tonne")):
        return DocumentType.bordereau_dechets
    if "contrat" in haystack:
        return DocumentType.contrat
    if any(k in haystack for k in ("attestation", "certificat")):
        return DocumentType.attestation
    return DocumentType.autre


def extract_document_fields(text: str, filename: str = "") -> tuple[dict[str, Any], int]:
    line_text = _normalize_ocr_text(text)
    normalized = " ".join(line_text.split())
    searchable = _normalize_for_search(f"{filename} {normalized}")
    fields: dict[str, Any] = {}
    is_steg_bill = any(keyword in searchable for keyword in ("steg", "societe tunisienne", "electricite et du gaz", "montant a payer", "facture sur releve"))
    is_water_bill = _is_water_bill(searchable)
    is_telecom_bill = _is_telecom_bill(searchable)

    if is_water_bill:
        fields["invoice_kind"] = "water"
    elif is_steg_bill:
        fields["invoice_kind"] = "energy"
    elif is_telecom_bill:
        fields["invoice_kind"] = "telecom"
    elif "facture" in searchable or "invoice" in searchable:
        fields["invoice_kind"] = "generic"

    dates = re.findall(r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", normalized)
    if dates:
        parsed = _parse_date(dates[0])
        if parsed:
            fields["document_date"] = parsed.isoformat()
    parsed_dates = [parsed for raw in dates if (parsed := _parse_date(raw))]
    period = _extract_labeled_period(normalized) or _extract_period(parsed_dates, prefer_earliest=is_steg_bill)
    if period:
        fields["period_start"] = period[0].isoformat()
        fields["period_end"] = period[1].isoformat()

    if is_steg_bill:
        fields["provider"] = "STEG"
    elif is_water_bill:
        fields["provider"] = "SONEDE"

    provider = _extract_provider(normalized, searchable)
    if provider:
        fields["provider"] = provider

    amount_due = _extract_amount_due(normalized)
    if amount_due is not None:
        fields["amount_due"] = amount_due

    amount = _extract_total_amount(normalized)
    if amount is not None:
        fields["amount"] = amount

    if is_steg_bill:
        consumption_values = _extract_consumption_from_indexes(line_text)
        if consumption_values:
            fields["quantity"] = consumption_values[0]
            fields["unit"] = "kWh"
        if len(consumption_values) > 1:
            fields["gas_quantity"] = consumption_values[1]
            fields["gas_unit"] = "m3"

    if is_steg_bill and ("quantity" not in fields or "gas_quantity" not in fields):
        priced_consumptions = _extract_consumption_from_prices(normalized)
        if "quantity" not in fields and priced_consumptions.get("electricity") is not None:
            fields["quantity"] = priced_consumptions["electricity"]
            fields["unit"] = "kWh"
        if "gas_quantity" not in fields and priced_consumptions.get("gas") is not None:
            fields["gas_quantity"] = priced_consumptions["gas"]
            fields["gas_unit"] = "m3"

    quantity_match = re.search(r"([0-9]+(?:[,.][0-9]+)?)\s*(k\s*w\s*h|kw\s?h|kwh|khw|m3|m³|t|tonnes?|litres?|l)\b", normalized, re.IGNORECASE)
    if quantity_match and "quantity" not in fields:
        fields["quantity"] = _parse_float(quantity_match.group(1))
        fields["unit"] = _normalize_unit(quantity_match.group(2))
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
    if supplier_match and "provider" not in fields:
        fields["provider"] = supplier_match.group(1).strip()

    if is_steg_bill:
        line_fields = _extract_steg_values_from_lines(line_text)
        for key, value in line_fields.items():
            fields.setdefault(key, value)

    if is_water_bill:
        line_fields = _extract_water_invoice_fields(line_text, normalized)
        for key, value in line_fields.items():
            if key in {"amount_due", "quantity", "unit"} or key not in fields:
                fields[key] = value

    generic_fields = _extract_generic_invoice_fields(line_text, normalized, searchable)
    for key, value in generic_fields.items():
        fields.setdefault(key, value)

    if "document_date" not in fields and fields.get("quantity") is not None and fields.get("unit"):
        fields["document_date"] = date.today().isoformat()

    confidence = _estimate_extraction_confidence(fields, is_steg_bill, is_water_bill)
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
    raw = _normalize_digits(str(value)).strip().replace("\u00a0", " ").replace(" ", "")
    raw = raw.replace("O", "0").replace("o", "0")
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _normalize_ocr_text(value: str) -> str:
    cleaned = _normalize_digits(value).replace("\u00a0", " ")
    cleaned = cleaned.replace("—", "-").replace("–", "-")
    cleaned = re.sub(r"[|¦]", " ", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())


def _normalize_for_search(value: str) -> str:
    value = _normalize_digits(value)
    replacements = str.maketrans({"é": "e", "è": "e", "ê": "e", "à": "a", "â": "a", "ù": "u", "ç": "c", "ï": "i", "î": "i", "'": " "})
    return value.lower().translate(replacements)


def _normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789"))


def _normalize_unit(value: str) -> str:
    normalized = _normalize_for_search(value).replace(" ", "").replace("³", "3")
    if normalized in {"kwh", "khw"} or normalized.startswith("kw"):
        return "kWh"
    if normalized in {"m3", "m"} or normalized.startswith("م"):
        return "m3"
    return value.strip()


def _extract_provider(text: str, searchable: str) -> str | None:
    if any(keyword in searchable for keyword in ("steg", "societe tunisienne", "electricite et du gaz")):
        return "STEG"
    if "sonede" in searchable or "eaux" in searchable:
        return "SONEDE"
    if "topnet" in searchable:
        return "Topnet"
    if "ooredoo" in searchable:
        return "Ooredoo"
    if "tunisie telecom" in searchable or "tt telecom" in searchable:
        return "Tunisie Telecom"
    if "orange" in searchable and any(keyword in searchable for keyword in ("facture", "mobile", "internet", "telephone")):
        return "Orange Tunisie"
    supplier_match = re.search(r"(?:fournisseur|supplier|prestataire)\s*[:=]\s*([A-Za-z0-9 &.'-]{2,80})", text, re.IGNORECASE)
    return supplier_match.group(1).strip() if supplier_match else None


def _is_water_bill(searchable: str) -> bool:
    if any(keyword in searchable for keyword in ("sonede", "consommation eau", "consommation d eau", "facture eau", "الماء", "المياه", "الماء الصالح", "استغلال وتوزيع المياه")):
        return True
    return bool(re.search(r"\b(eau|eaux|water)\b", searchable))


def _is_telecom_bill(searchable: str) -> bool:
    return any(
        keyword in searchable
        for keyword in (
            "topnet",
            "ooredoo",
            "orange tunisie",
            "tunisie telecom",
            "telecom",
            "internet",
            "adsl",
            "fibre",
            "forfait",
            "telephone",
            "mobile",
        )
    )


def _extract_total_amount(text: str) -> float | None:
    for label_pattern in (r"montant\s+total", r"total\s+ttc", r"total\s+consommation\s*&\s*services"):
        label_match = re.search(rf"(?:{label_pattern})(.{{0,45}})", text, re.IGNORECASE)
        if label_match:
            parsed = _first_amount_in_text(label_match.group(1), min_value=10)
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


def _first_amount_in_text(text: str, min_value: float = 0) -> float | None:
    amounts = _amount_candidates(text, min_value=min_value)
    return amounts[0] if amounts else None


def _amount_candidates(text: str, min_value: float = 0) -> list[float]:
    amounts: list[float] = []
    for raw in re.findall(r"\b([0-9]+[,.][0-9]{2,3})\b", text):
        parsed = _parse_float(raw)
        if parsed is not None and min_value <= parsed <= 100000:
            amounts.append(parsed)
    for match in re.finditer(r"(?<![0-9,.])([0-9]{1,3})[ \t]+([0-9]{3})(?![0-9,.])", text):
        parsed = _parse_float(f"{match.group(1)}.{match.group(2)}")
        if parsed is not None and min_value <= parsed <= 100000 and parsed not in amounts:
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


def _extract_labeled_period(text: str) -> tuple[date, date] | None:
    date_pattern = r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})"
    patterns = (
        rf"(?:periode|période|du|from)\D{{0,40}}{date_pattern}\D{{0,40}}(?:au|to|jusqu)\D{{0,40}}{date_pattern}",
        rf"{date_pattern}\D{{0,25}}(?:au|to|jusqu)\D{{0,25}}{date_pattern}",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        parsed_dates = [_parse_date(group) for group in match.groups()]
        clean_dates = [value for value in parsed_dates if value is not None]
        if len(clean_dates) >= 2 and clean_dates[0] < clean_dates[1]:
            return clean_dates[0], clean_dates[1]
    return None


def _extract_steg_values_from_lines(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line.strip()]
    fields: dict[str, Any] = {}

    for index, line in enumerate(lines):
        searchable = _normalize_for_search(line)
        nearby = " ".join(lines[index : index + 3])
        nearby_searchable = _normalize_for_search(nearby)

        if "montant total" in nearby_searchable and "amount" not in fields:
            amount = _last_amount_in_text(nearby, min_value=10)
            if amount is not None:
                fields["amount"] = amount

        if "montant a payer" in nearby_searchable and "amount_due" not in fields:
            due = _last_amount_in_text(nearby, min_value=50)
            if due is not None:
                fields["amount_due"] = due

        if "total" not in searchable and any(keyword in searchable for keyword in ("electricite", "eclairage")) and "quantity" not in fields:
            quantity = _best_steg_quantity_near_line(nearby)
            if quantity is not None:
                fields["quantity"] = quantity
                fields["unit"] = "kWh"

        if "total" not in searchable and "gaz" in searchable and "gas_quantity" not in fields:
            quantity = _best_steg_quantity_near_line(nearby)
            if quantity is not None:
                fields["gas_quantity"] = quantity
                fields["gas_unit"] = "m3"

    if "quantity" not in fields or "gas_quantity" not in fields:
        index_values = _extract_consumption_from_indexes(text)
        if index_values:
            fields.setdefault("quantity", index_values[0])
            fields.setdefault("unit", "kWh")
        if len(index_values) > 1:
            fields.setdefault("gas_quantity", index_values[1])
            fields.setdefault("gas_unit", "m3")

    return fields


def _best_steg_quantity_near_line(text: str) -> float | None:
    quantity_label = re.search(r"(?:quantit[eé]|consommation)\D{0,20}([0-9]+(?:[,.][0-9]+)?)", text, re.IGNORECASE)
    if quantity_label:
        parsed = _parse_float(quantity_label.group(1))
        if parsed is not None and 1 <= parsed <= 50000:
            return parsed

    index_values = _extract_consumption_from_indexes(text)
    if index_values:
        return index_values[0]

    numbers = [_parse_float(match.group(1)) for match in re.finditer(r"\b([0-9]+(?:[,.][0-9]+)?)\b", text)]
    clean_numbers = [value for value in numbers if value is not None and 1 <= value <= 50000]
    integer_candidates = [value for value in clean_numbers if float(value).is_integer() and value not in {4, 5, 7, 19}]
    return integer_candidates[0] if integer_candidates else None


def _extract_water_invoice_fields(line_text: str, normalized: str) -> dict[str, Any]:
    fields: dict[str, Any] = {"provider": "SONEDE", "invoice_kind": "water"}

    quantity = _extract_water_quantity(line_text, normalized)
    if quantity is not None:
        fields["quantity"] = quantity
        fields["unit"] = "m3"

    due = _extract_water_amount_due(line_text, normalized)
    if due is None:
        due = _last_amount_in_text(normalized, min_value=1)
    if due is not None:
        fields["amount_due"] = due

    amount = _extract_total_amount(normalized)
    if amount is not None:
        fields["amount"] = amount

    return fields


def _extract_generic_invoice_fields(line_text: str, normalized: str, searchable: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    provider = _extract_provider(normalized, searchable)
    if provider:
        fields["provider"] = provider

    if _is_telecom_bill(searchable):
        fields["invoice_kind"] = "telecom"
        fields["service"] = _extract_telecom_service(searchable)
    elif "invoice_kind" not in fields and ("facture" in searchable or "invoice" in searchable):
        fields["invoice_kind"] = "generic"

    due = _extract_amount_due_from_lines(line_text)
    if due is not None:
        fields["amount_due"] = due
    elif "facture" in searchable or "invoice" in searchable:
        amounts = _amount_candidates(normalized, min_value=1)
        if amounts:
            fields["amount_due"] = max(amounts)

    amount = _extract_total_amount(normalized)
    if amount is not None:
        fields["amount"] = amount

    quantity = _extract_explicit_quantity_with_unit(normalized)
    if quantity is not None:
        fields["quantity"] = quantity[0]
        fields["unit"] = quantity[1]

    return fields


def _extract_water_quantity(line_text: str, normalized: str) -> float | None:
    explicit = _extract_explicit_quantity_with_unit(normalized, units=("m3", "m³", "م3", "م³"))
    index_values = _extract_consumption_from_indexes(line_text, max_difference=2000)
    cloud_quantity = _best_water_quantity_from_number_cloud(normalized)
    if explicit is not None and (explicit[0] >= 5 or not index_values and cloud_quantity is None):
        return explicit[0]

    labeled = re.search(r"(?:consommation|quantit[eé]|volume|استهلاك)\D{0,45}([0-9]+(?:[,.][0-9]+)?)", normalized, re.IGNORECASE)
    if labeled:
        parsed = _parse_float(labeled.group(1))
        if parsed is not None and 1 <= parsed <= 2000:
            return parsed

    lines = [line for line in line_text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        searchable = _normalize_for_search(line)
        if not any(keyword in searchable for keyword in ("consommation", "quantite", "volume", "eau", "الماء", "المياه", "استهلاك")):
            continue
        nearby = " ".join(lines[max(0, index - 1) : index + 3])
        labeled = re.search(r"(?:consommation|quantit[eé]|volume|استهلاك)\D{0,30}([0-9]+(?:[,.][0-9]+)?)", nearby, re.IGNORECASE)
        if labeled:
            parsed = _parse_float(labeled.group(1))
            if parsed is not None and 1 <= parsed <= 2000:
                return parsed
        integers = _small_integer_candidates(nearby)
        if integers:
            return integers[0]

    if index_values:
        return index_values[0]

    return cloud_quantity


def _extract_explicit_quantity_with_unit(text: str, units: tuple[str, ...] = ("kwh", "khw", "kw h", "m3", "m³", "م3", "م³", "t", "tonne", "tonnes", "l", "litre", "litres")) -> tuple[float, str] | None:
    unit_pattern = "|".join(re.escape(unit) for unit in units)
    patterns = (
        rf"([0-9]+(?:[,.][0-9]+)?)\s*(?:{unit_pattern})",
        rf"(?:{unit_pattern})\s*([0-9]+(?:[,.][0-9]+)?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        parsed = _parse_float(match.group(1))
        if parsed is None or parsed <= 0:
            continue
        unit_match = re.search(unit_pattern, match.group(0), re.IGNORECASE)
        unit = _normalize_unit(unit_match.group(0)) if unit_match else ""
        return parsed, unit
    return None


def _extract_amount_due_from_lines(line_text: str) -> float | None:
    lines = [line for line in line_text.splitlines() if line.strip()]
    payment_keywords = (
        "montant a payer",
        "montant à payer",
        "net a payer",
        "net à payer",
        "total a payer",
        "total à payer",
        "a payer",
        "à payer",
        "payer",
        "المبلغ",
        "المعلوم",
        "الدفع",
        "المجموع",
    )
    total_keywords = ("montant total", "total ttc", "total", "ttc", "montant")
    for keywords in (payment_keywords, total_keywords):
        for index, line in enumerate(lines):
            searchable = _normalize_for_search(line)
            if not any(keyword in searchable for keyword in keywords):
                continue
            nearby = " ".join(lines[max(0, index - 1) : index + 2])
            amounts = _amount_candidates(nearby, min_value=1)
            if amounts:
                return amounts[-1]
    return None


def _extract_water_amount_due(line_text: str, normalized: str) -> float | None:
    lines = [line for line in line_text.splitlines() if line.strip()]
    payment_keywords = (
        "montant a payer",
        "montant à payer",
        "a payer",
        "à payer",
        "total",
        "ttc",
        "المبلغ",
        "المعلوم",
        "الدفع",
        "للدفع",
        "للاستخلاص",
        "الاستخلاص",
        "المجموع",
    )
    for index, line in enumerate(lines):
        searchable = _normalize_for_search(line)
        if not any(keyword in searchable for keyword in payment_keywords):
            continue
        nearby = " ".join(lines[max(0, index - 1) : index + 2])
        amounts = _amount_candidates(nearby, min_value=1)
        clean_amounts = [amount for amount in amounts if 1 <= amount <= 2000]
        if clean_amounts:
            return clean_amounts[-1]

    amounts = [amount for amount in _amount_candidates(normalized, min_value=1) if 1 <= amount <= 2000]
    if not amounts:
        return None
    preferred = [amount for amount in amounts if amount >= 5 and not float(amount).is_integer()]
    return preferred[-1] if preferred else amounts[-1]


def _small_integer_candidates(text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(r"(?<![0-9,.])([0-9]{1,4})(?![0-9,.])", text):
        parsed = _parse_float(match.group(1))
        if parsed is None:
            continue
        if 5 <= parsed <= 300 and parsed not in {5, 7, 12, 16, 17, 18, 19, 20, 100} and parsed not in values:
            values.append(parsed)
    return values


def _best_water_quantity_from_number_cloud(text: str) -> float | None:
    numbers = [_parse_float(match.group(1)) for match in re.finditer(r"\b([0-9]{1,6}(?:[,.][0-9]+)?)\b", text)]
    clean_numbers = [value for value in numbers if value is not None]
    common_quantities = [
        value
        for value in clean_numbers
        if float(value).is_integer() and 5 <= value <= 300 and value not in {5, 7, 12, 16, 17, 18, 19, 20, 100}
    ]
    repeated = [value for value in common_quantities if common_quantities.count(value) > 1]
    if repeated:
        return repeated[0]
    if common_quantities:
        return common_quantities[0]
    return None


def _extract_telecom_service(searchable: str) -> str:
    if "fibre" in searchable:
        return "Internet fibre"
    if "adsl" in searchable:
        return "Internet ADSL"
    if "internet" in searchable:
        return "Internet"
    if "mobile" in searchable or "forfait" in searchable:
        return "Forfait mobile"
    if "telephone" in searchable or "telecom" in searchable:
        return "Téléphonie"
    return "Service télécom"


def _extract_consumption_from_indexes(text: str, max_difference: int = 50000) -> list[float]:
    values: list[float] = []
    without_dates = re.sub(r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b", " ", text)
    without_dates = re.sub(r"\b\d{2}[-/.]\d{2}[-/.]\d{4}\b", " ", without_dates)
    for line in without_dates.splitlines() or [without_dates]:
        integer_tokens = [int(match.group(1)) for match in re.finditer(r"\b([0-9]{4,6})\b", line)]
        for previous, current in zip(integer_tokens, integer_tokens[1:], strict=False):
            difference = abs(previous - current)
            if 5 <= difference <= max_difference and difference not in values:
                values.append(float(difference))
    return values[:2]


def _extract_consumption_from_prices(text: str) -> dict[str, float]:
    searchable = _normalize_for_search(text)
    gas_index = searchable.find("gaz")
    electricity_text = text[:gas_index] if gas_index >= 0 else text
    gas_text = text[gas_index:] if gas_index >= 0 else ""

    electricity = _best_quantity_from_price_pairs(electricity_text)
    gas = _best_quantity_from_price_pairs(gas_text)
    if electricity is None or gas is None:
        fallback = _quantities_from_price_pairs(text)
        if electricity is None and fallback:
            electricity = fallback[0]
        if gas is None and len(fallback) > 1:
            gas = next((value for value in fallback[1:] if value != electricity), None)

    result: dict[str, float] = {}
    if electricity is not None:
        result["electricity"] = electricity
    if gas is not None:
        result["gas"] = gas
    return result


def _best_quantity_from_price_pairs(text: str) -> float | None:
    quantities = _quantities_from_price_pairs(text)
    return max(quantities) if quantities else None


def _quantities_from_price_pairs(text: str) -> list[float]:
    numbers = [_parse_float(match.group(1)) for match in re.finditer(r"\b([0-9]+[,.][0-9]{3})\b", text)]
    decimals = [value for value in numbers if value is not None]
    quantities: list[float] = []
    for amount, unit_price in zip(decimals, decimals[1:], strict=False):
        if amount < 1 or unit_price <= 0 or unit_price >= 2:
            continue
        quantity = round(amount / unit_price)
        if 5 <= quantity <= 50000 and abs((unit_price * quantity) - amount) <= 0.02 and float(quantity) not in quantities:
            quantities.append(float(quantity))
    return quantities


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


def _estimate_extraction_confidence(fields: dict[str, Any], is_steg_bill: bool, is_water_bill: bool = False) -> int:
    confidence = min(95, 45 + len(fields) * 10)
    if not is_steg_bill and not is_water_bill:
        return confidence

    suspicious = False
    amount_due = _parse_float(fields.get("amount_due"))
    amount = _parse_float(fields.get("amount"))
    quantity = _parse_float(fields.get("quantity"))
    gas_quantity = _parse_float(fields.get("gas_quantity"))

    expected_provider = "STEG" if is_steg_bill else "SONEDE"
    if fields.get("provider") != expected_provider:
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
    raw = str(value).strip().replace(".", "-").replace("/", "-")
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None
