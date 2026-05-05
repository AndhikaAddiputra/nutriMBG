import csv
import difflib
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from app.core.settings import settings

NUTRIENTS = ["protein", "carbohydrate", "fat", "fiber", "iron", "vitamin_a"]

AKG_LEVELS = {
    "SD": ["7-9 tahun", "10-12 tahun"],
    "SMP": ["13-15 tahun"],
    "SMA": ["16-18 tahun"],
}

_AKG_HEADER_MAP = {
    "protein (g)": "protein",
    "karbohidrat (g)": "carbohydrate",
    "lemak total (g)": "fat",
    "serat (g)": "fiber",
    "besi (mg)": "iron",
    "vit a (re)": "vitamin_a",
}

_TKPI_COLUMNS = {
    "PROTEIN": "protein",
    "LEMAK": "fat",
    "KH": "carbohydrate",
    "SERAT": "fiber",
    "BESI": "iron",
    "RETINOL": "retinol",
    "KAR-TOTAL": "carotene_total",
}

_STOP_PHRASES = {
    "secukupnya",
    "sesuai selera",
    "optional",
    "opsional",
    "untuk",
    "sbg",
}

_UNIT_WORDS = {
    "kg",
    "kilogram",
    "g",
    "gr",
    "gram",
    "mg",
    "ml",
    "l",
    "liter",
    "sdm",
    "sdt",
    "sendok",
    "makan",
    "teh",
    "buah",
    "butir",
    "ekor",
    "lembar",
    "siung",
    "ruas",
    "batang",
    "potong",
    "gelas",
}

_COOKING_WORDS = {
    "goreng",
    "gulai",
    "oseng",
    "tumis",
    "suwir",
    "bakar",
    "rebus",
    "kukus",
    "panggang",
    "pepes",
    "balado",
    "sambal",
    "sambel",
    "matah",
    "rica",
    "woku",
    "saus",
    "saos",
    "kuah",
    "bumbu",
    "kecap",
}


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _parse_float(value: str) -> float:
    if value is None:
        return 0.0
    value = value.strip().replace(",", ".")
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def normalize_ingredient_name(value: str) -> str:
    text = value.lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    for phrase in _STOP_PHRASES:
        text = text.replace(phrase, " ")
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = [
        token
        for token in text.split()
        if token not in _UNIT_WORDS and token not in _COOKING_WORDS
    ]
    return " ".join(tokens).strip()


def _find_header_row(lines: List[str], starts_with: str) -> int:
    for idx, line in enumerate(lines):
        if line.strip().startswith(starts_with):
            return idx
    return 0


@lru_cache(maxsize=1)
def load_tkpi_index() -> Dict[str, Dict[str, float]]:
    dataset_dir = Path(settings.dataset_dir)
    path = dataset_dir / "kandungan-gizi" / "TKPI.csv"
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = _find_header_row(lines, "KODE,")
    reader = csv.DictReader(lines[header_idx:])
    index: Dict[str, Dict[str, float]] = {}
    for row in reader:
        name = (row.get("NAMA BAHAN") or "").strip()
        if not name:
            continue
        normalized_name = normalize_ingredient_name(name)
        if not normalized_name:
            continue
        values: Dict[str, float] = {}
        for col, target in _TKPI_COLUMNS.items():
            values[target] = _parse_float(row.get(col, ""))
        vitamin_a = values.get("retinol", 0.0)
        carotene = values.get("carotene_total", 0.0)
        if carotene:
            vitamin_a += carotene / 6.0
        values["vitamin_a"] = vitamin_a
        for key in ["retinol", "carotene_total"]:
            values.pop(key, None)
        index[normalized_name] = values
    return index


@lru_cache(maxsize=1)
def load_akg_targets() -> Dict[str, Dict[str, float]]:
    dataset_dir = Path(settings.dataset_dir)
    path = dataset_dir / "akg" / "akg_indonesia_ekstraksi.csv"
    targets_by_age: Dict[str, Dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            age = (row.get("Kelompok Umur") or "").strip()
            if not age:
                continue
            normalized_row = {_normalize_header(k): v for k, v in row.items() if k}
            nutrient_values = {}
            for header, nutrient in _AKG_HEADER_MAP.items():
                nutrient_values[nutrient] = _parse_float(normalized_row.get(header, ""))
            targets_by_age[age] = nutrient_values

    level_targets: Dict[str, Dict[str, float]] = {}
    for level, ages in AKG_LEVELS.items():
        totals = {nutrient: 0.0 for nutrient in NUTRIENTS}
        counts = {nutrient: 0 for nutrient in NUTRIENTS}
        for age in ages:
            age_values = targets_by_age.get(age)
            if not age_values:
                continue
            for nutrient in NUTRIENTS:
                value = age_values.get(nutrient, 0.0)
                if value > 0:
                    totals[nutrient] += value
                    counts[nutrient] += 1
        level_targets[level] = {
            nutrient: (totals[nutrient] / counts[nutrient] if counts[nutrient] else 0.0)
            for nutrient in NUTRIENTS
        }
    return level_targets


@lru_cache(maxsize=1)
def load_alias_map() -> Dict[str, str]:
    dataset_dir = Path(settings.dataset_dir)
    path = dataset_dir / "aliases.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        alias_map: Dict[str, str] = {}
        for row in reader:
            alias = normalize_ingredient_name(row.get("alias", "") or "")
            canonical = normalize_ingredient_name(row.get("canonical", "") or "")
            if alias and canonical:
                alias_map[alias] = canonical
    return alias_map


def _match_tkpi_key(name: str, keys_list: List[str]) -> Tuple[str, float]:
    normalized = normalize_ingredient_name(name)
    if not normalized:
        return "", 0.0
    alias_map = load_alias_map()
    if normalized in alias_map:
        normalized = alias_map[normalized]
    if normalized in keys_list:
        return normalized, 1.0
    for key in keys_list:
        if normalized in key or key in normalized:
            return key, 0.9
    matches = difflib.get_close_matches(normalized, keys_list, n=1, cutoff=0.82)
    if matches:
        return matches[0], 0.82
    return "", 0.0


def compute_totals_from_items(
    items: List[Dict[str, float]],
    tkpi_index: Dict[str, Dict[str, float]],
) -> Tuple[Dict[str, float], List[str]]:
    totals = {nutrient: 0.0 for nutrient in NUTRIENTS}
    unmatched: List[str] = []
    keys = list(tkpi_index.keys())
    for item in items:
        name = item.get("name") if isinstance(item, dict) else getattr(item, "name", "")
        weight = item.get("weight_gram") if isinstance(item, dict) else getattr(item, "weight_gram", 0.0)
        if not name:
            continue
        weight_value = float(weight or 0.0)
        if weight_value <= 0:
            continue
        matched_key, _ = _match_tkpi_key(str(name), keys)
        if not matched_key:
            unmatched.append(str(name))
            continue
        nutrient_values = tkpi_index.get(matched_key, {})
        factor = weight_value / 100.0
        for nutrient in NUTRIENTS:
            totals[nutrient] += float(nutrient_values.get(nutrient, 0.0)) * factor
    return totals, unmatched


def compute_ratios(totals: Dict[str, float], targets: Dict[str, float]) -> Dict[str, float]:
    ratios: Dict[str, float] = {}
    for nutrient in NUTRIENTS:
        target_value = float(targets.get(nutrient, 0.0))
        if target_value <= 0:
            ratios[nutrient] = 0.0
        else:
            ratios[nutrient] = float(totals.get(nutrient, 0.0)) / target_value
    return ratios


def label_deficiency(ratio: float) -> str:
    if ratio >= 1.0:
        return "Cukup"
    if ratio >= 0.8:
        return "Perlu Perhatian"
    return "Defisien"


def compute_score(ratios: Dict[str, float], cap: float = 1.2) -> float:
    if not ratios:
        return 0.0
    capped = [min(float(ratios.get(nutrient, 0.0)), cap) for nutrient in NUTRIENTS]
    return round(sum(capped) / len(capped) * 100.0, 2)
