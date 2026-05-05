import re
from typing import Dict, List, Optional

_UNIT_GRAMS = {
    "kg": 1000.0,
    "kilogram": 1000.0,
    "g": 1.0,
    "gr": 1.0,
    "gram": 1.0,
    "mg": 0.001,
    "ml": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "sdm": 15.0,
    "sendok makan": 15.0,
    "sdt": 5.0,
    "sendok teh": 5.0,
    "gelas": 200.0,
    "buah": 50.0,
    "butir": 50.0,
    "ekor": 1000.0,
    "lembar": 5.0,
    "siung": 3.0,
    "ruas": 5.0,
    "batang": 30.0,
    "potong": 50.0,
    "sachet": 10.0,
    "bungkus": 10.0,
}

_UNIT_KEYS = sorted(_UNIT_GRAMS.keys(), key=len, reverse=True)

_QUANTITY_RE = re.compile(r"(\d+\s+\d+/\d+|\d+/\d+|\d+[.,]?\d*)")

_STOP_PHRASES = {
    "secukupnya",
    "sesuai selera",
    "optional",
    "opsional",
}


def _parse_quantity(token: str) -> Optional[float]:
    token = token.strip().replace(",", ".")
    if not token:
        return None
    if " " in token and "/" in token:
        parts = token.split()
        if len(parts) == 2:
            whole = _parse_quantity(parts[0]) or 0.0
            frac = _parse_quantity(parts[1]) or 0.0
            return whole + frac
    if "/" in token:
        num, denom = token.split("/", 1)
        try:
            return float(num) / float(denom)
        except ValueError:
            return None
    try:
        return float(token)
    except ValueError:
        return None


def _find_unit(text: str) -> Optional[str]:
    for unit in _UNIT_KEYS:
        pattern = r"\b" + re.escape(unit) + r"\b"
        if re.search(pattern, text):
            return unit
    return None


def _strip_quantity_and_unit(text: str, quantity_token: Optional[str], unit: Optional[str]) -> str:
    cleaned = text
    if quantity_token:
        cleaned = cleaned.replace(quantity_token, " ")
    if unit:
        cleaned = re.sub(r"\b" + re.escape(unit) + r"\b", " ", cleaned)
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)
    for phrase in _STOP_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def parse_ingredient_line(line: str) -> Optional[Dict[str, float]]:
    if not line:
        return None
    text = line.strip().strip('"').lower()
    if not text or text in _STOP_PHRASES:
        return None
    quantity_match = _QUANTITY_RE.search(text)
    quantity_token = quantity_match.group(0) if quantity_match else None
    quantity_value = _parse_quantity(quantity_token) if quantity_token else None
    unit = _find_unit(text)
    name = _strip_quantity_and_unit(text, quantity_token, unit)
    if not name:
        name = text
    if quantity_value is None:
        weight = 100.0
    elif unit:
        weight = quantity_value * _UNIT_GRAMS.get(unit, 1.0)
    else:
        weight = quantity_value
    return {"name": name, "weight_gram": float(weight)}


def parse_ingredient_block(block: str) -> List[Dict[str, float]]:
    if not block:
        return []
    parts = [part.strip() for part in block.split("--") if part.strip()]
    items: List[Dict[str, float]] = []
    for part in parts:
        parsed = parse_ingredient_line(part)
        if parsed:
            items.append(parsed)
    return items
