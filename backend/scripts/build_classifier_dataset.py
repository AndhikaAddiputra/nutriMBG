import csv
import sys
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.settings import settings
from app.ml.ingredient_parser import parse_ingredient_block
from app.ml.nutrition import (
    AKG_LEVELS,
    NUTRIENTS,
    compute_ratios,
    compute_score,
    compute_totals_from_items,
    label_deficiency,
    load_akg_targets,
    load_tkpi_index,
)


def build_dataset() -> None:
    dataset_dir = Path(settings.dataset_dir)
    menu_dir = dataset_dir / "menu-nusantara"
    output_dir = dataset_dir / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "menu_classifier_dataset.csv"
    unmatched_path = output_dir / "unmatched_ingredients.csv"

    tkpi_index = load_tkpi_index()
    akg_targets = load_akg_targets()

    unmatched_counter: Counter[str] = Counter()
    rows = []

    for menu_file in sorted(menu_dir.glob("dataset-*.csv")):
        with menu_file.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = (row.get("Title") or "").strip()
                ingredients = row.get("Ingredients") or ""
                if not title or not ingredients:
                    continue
                items = parse_ingredient_block(ingredients)
                totals, unmatched = compute_totals_from_items(items, tkpi_index)
                if all(value == 0.0 for value in totals.values()):
                    continue
                for item in unmatched:
                    unmatched_counter[item.lower()] += 1
                for level in AKG_LEVELS.keys():
                    targets = akg_targets.get(level, {})
                    ratios = compute_ratios(totals, targets)
                    labels = {nutrient: label_deficiency(ratios[nutrient]) for nutrient in NUTRIENTS}
                    score = compute_score(ratios)
                    rows.append(
                        {
                            "menu_title": title,
                            "source_file": menu_file.name,
                            "education_level": level,
                            **{nutrient: round(totals[nutrient], 4) for nutrient in NUTRIENTS},
                            **{f"ratio_{nutrient}": round(ratios[nutrient], 6) for nutrient in NUTRIENTS},
                            **{f"label_{nutrient}": labels[nutrient] for nutrient in NUTRIENTS},
                            "score": score,
                        }
                    )

    if not rows:
        raise RuntimeError("Dataset kosong. Periksa file menu-nusantara dan parsing ingredient.")

    fieldnames = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with unmatched_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ingredient", "count"])
        for ingredient, count in unmatched_counter.most_common():
            writer.writerow([ingredient, count])

    print(f"Dataset tersimpan di {output_path}")
    print(f"Unmatched ingredients tersimpan di {unmatched_path}")


if __name__ == "__main__":
    build_dataset()
