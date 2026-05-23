"""
scripts/evaluate_model.py
==========================
Comprehensive model evaluation.

Computes:
  - Regression: MAE, RMSE, R² (score prediction)
  - Classification: Hamming Loss, F1-Score per nutrient, Subset Accuracy

Usage:
  python scripts/evaluate_model.py
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.settings import settings

NUTRIENTS = ["protein", "carbohydrate", "fat", "fiber", "iron", "vitamin_a"]
LABEL_COLS = [f"label_{n}" for n in NUTRIENTS]


def _label_from_ratio(ratio: float) -> str:
    if ratio >= 1.0:
        return "Cukup"
    if ratio >= 0.8:
        return "Perlu Perhatian"
    return "Defisien"


def evaluate() -> dict:
    dataset_path = Path(settings.dataset_dir) / "processed" / "menu_classifier_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan. Jalankan build_classifier_dataset.py dulu.")

    df = pd.read_csv(dataset_path)
    feature_cols = [col for col in df.columns if col.startswith("ratio_")]

    X = df[feature_cols]
    y_score = df["score"]

    # --- Regression evaluation ---
    X_train, X_test, y_train, y_test = train_test_split(X, y_score, test_size=0.2, random_state=42)

    bundle = joblib.load(settings.classifier_model_path)
    model = bundle["model"]

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)

    # --- Classification evaluation (on test set only) ---
    ratio_cols = feature_cols
    test_indices = X_test.index
    df_test = df.iloc[test_indices]

    y_true_labels = df_test[LABEL_COLS].values
    ratio_values = df_test[ratio_cols].values
    y_pred_labels = np.array([
        [_label_from_ratio(ratio) for ratio in row]
        for row in ratio_values
    ])

    ham_loss = np.sum(y_true_labels != y_pred_labels) / y_true_labels.size
    subset_acc = np.mean([np.array_equal(y_true_labels[i], y_pred_labels[i]) for i in range(len(y_true_labels))])

    per_nutrient_f1 = {}
    per_nutrient_acc = {}
    for i, nutrient in enumerate(NUTRIENTS):
        f1 = f1_score(y_true_labels[:, i], y_pred_labels[:, i], average="weighted", zero_division=0)
        per_nutrient_f1[nutrient] = round(f1, 4)
        acc = np.mean(y_true_labels[:, i] == y_pred_labels[:, i])
        per_nutrient_acc[nutrient] = round(acc, 4)

    results = {
        "dataset_size": len(df),
        "test_size": len(df_test),
        "regression": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
        },
        "classification": {
            "hamming_loss": round(ham_loss, 4),
            "subset_accuracy": round(subset_acc, 4),
            "per_nutrient_f1": per_nutrient_f1,
            "per_nutrient_accuracy": per_nutrient_acc,
        },
    }

    return results


if __name__ == "__main__":
    results = evaluate()
    print(json.dumps(results, indent=2))

    output_path = Path(settings.dataset_dir) / "processed" / "evaluation_report.json"
    with output_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"\nLaporan evaluasi tersimpan di {output_path}")
