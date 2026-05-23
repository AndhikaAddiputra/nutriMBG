"""
scripts/generate_aliases.py
============================
Auto-generate alias mappings from TKPI ingredient names.

Strategy
--------
1. Parse TKPI CSV, extract all ingredient names
2. Normalize each name with the same function used in nutrition.py
3. For names whose normalized form differs from the raw name,
   create an alias → canonical mapping

Usage
-----
python scripts/generate_aliases.py
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TKPI_PATH = ROOT / "dataset" / "kandungan-gizi" / "TKPI.csv"
ALIASES_PATH = ROOT / "dataset" / "aliases.csv"

_STOP_PHRASES = {
    "secukupnya", "sesuai selera", "optional", "opsional",
    "untuk", "sbg",
}

_UNIT_WORDS = {
    "kg", "kilogram", "g", "gr", "gram", "mg", "ml", "l", "liter",
    "sdm", "sdt", "sendok", "makan", "teh", "buah", "butir", "ekor",
    "lembar", "siung", "ruas", "batang", "potong", "gelas",
}

_COOKING_WORDS = {
    "goreng", "gulai", "oseng", "tumis", "suwir", "bakar", "rebus",
    "kukus", "panggang", "pepes", "balado", "sambal", "sambel",
    "matah", "rica", "woku", "saus", "saos", "kuah", "bumbu",
    "kecap", "bacem", "bistik", "rendang", "semur", "sop", "soto",
    "opor", "kari", "kare", "lodeh", "sayur", "urap", "pecel",
    "kering", "campur", "isi", "lapis", "gulung", "panggang",
}


def normalize_name(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = [
        t for t in text.split()
        if t not in _UNIT_WORDS and t not in _COOKING_WORDS and t not in _STOP_PHRASES
    ]
    return " ".join(tokens).strip()


def main():
    if not TKPI_PATH.exists():
        print(f"TKPI file tidak ditemukan: {TKPI_PATH}")
        sys.exit(1)

    lines = TKPI_PATH.read_text(encoding="utf-8-sig").splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("KODE,"):
            header_idx = i
            break

    if header_idx is None:
        print("Header TKPI tidak ditemukan.")
        sys.exit(1)

    reader = csv.DictReader(lines[header_idx:])
    raw_names = set()
    for row in reader:
        name = (row.get("NAMA BAHAN") or "").strip().strip('"')
        if name:
            raw_names.add(name)

    canonical_map: dict[str, str] = {}
    for name in raw_names:
        canonical = normalize_name(name)
        raw_lower = name.lower().strip()
        if canonical and raw_lower != canonical:
            canonical_map[raw_lower] = canonical

    existing_aliases = set()
    if ALIASES_PATH.exists():
        with ALIASES_PATH.open(encoding="utf-8-sig") as f:
            existing = list(csv.DictReader(f))
            for row in existing:
                existing_aliases.add(row["alias"])

    new_rows = []
    for raw_alias, canonical in sorted(canonical_map.items()):
        if raw_alias in existing_aliases:
            continue
        new_rows.append({"alias": raw_alias, "canonical": canonical})

    if not new_rows:
        print("Tidak ada alias baru yang ditemukan.")
        sys.exit(0)

    with ALIASES_PATH.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["alias", "canonical"])
        for row in new_rows:
            writer.writerow(row)

    print(f"Berhasil menambahkan {len(new_rows)} alias baru ke {ALIASES_PATH}")


if __name__ == "__main__":
    main()
