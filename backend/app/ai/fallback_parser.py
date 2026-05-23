from typing import Dict, List, Tuple

import re


def parse_menu_fallback(text: str) -> Tuple[List[Dict[str, float]], List[str]]:
    """
    Regex-based fallback parser for structured menu text.
    Handles patterns like:
      - "Nasi putih 150 gram"
      - "ayam goreng 100gr"
      - "telur 2 butir"
      - "wortel 50 g"

    Returns (items, unmatched_tokens).
    """
    items: List[Dict[str, float]] = []
    unmatched: List[str] = []
    seen_names: set = set()

    # Pattern: ingredient name followed by quantity and unit
    # e.g., "Nasi putih 150 gram", "ayam goreng 100gr", "wortel 50g"
    pattern = re.compile(
        r"([a-zA-Z\s]+?)\s*"            # name (capture group 1)
        r"(\d+(?:[.,]\d+)?)\s*"          # amount (capture group 2)
        r"(gram|gr|g|kg|ml|l|liter|butir|buah|sdm|sdt|gelas|mangkok|ekor|potong|iris|slice|pcs|biji)?"
        r"(?:\s|,|$|\.)",
        re.IGNORECASE,
    )

    # Also handle list-like formats: "- Nasi 150gr"
    list_pattern = re.compile(r"[-–•*]\s*")

    # Try to split by comma or "dan" for multi-item parsing
    segments = re.split(r"\s*,\s*|\s+dan\s+", text.strip())

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # Remove list markers
        segment = list_pattern.sub("", segment).strip()

        match = pattern.search(segment)
        if match:
            name = match.group(1).strip().lower()
            amount_str = match.group(2).replace(",", ".")
            unit = (match.group(3) or "").lower()

            try:
                amount = float(amount_str)
            except ValueError:
                unmatched.append(segment)
                continue

            # Normalize unit to grams
            multiplier = _unit_to_grams(unit)
            weight = amount * multiplier

            # Merge duplicates (same name, sum weights)
            if name in seen_names:
                for item in items:
                    if item["name"] == name:
                        item["weight_gram"] += weight
                        break
            else:
                seen_names.add(name)
                items.append({"name": name, "weight_gram": weight})
        else:
            unmatched.append(segment)

    return items, unmatched


def _unit_to_grams(unit: str) -> float:
    mapping = {
        "gram": 1.0, "gr": 1.0, "g": 1.0,
        "kg": 1000.0,
        "ml": 1.0, "liter": 1000.0, "l": 1000.0,
        "butir": 50.0,     # 1 butir telur ≈ 50g
        "buah": 100.0,     # 1 buah pisang/apel ≈ 100g
        "sdm": 15.0,       # 1 sdm ≈ 15g
        "sdt": 5.0,        # 1 sdt ≈ 5g
        "gelas": 200.0,    # 1 gelas ≈ 200ml
        "mangkok": 250.0,  # 1 mangkok ≈ 250ml
        "ekor": 75.0,      # 1 ekor ikan/lele ≈ 75g
        "potong": 50.0,    # 1 potong ayam ≈ 50g
        "iris": 10.0,      # 1 iris ≈ 10g
        "slice": 10.0,
        "pcs": 50.0,       # 1 pcs ≈ 50g
        "biji": 10.0,      # 1 biji ≈ 10g
    }
    return mapping.get(unit, 1.0)
