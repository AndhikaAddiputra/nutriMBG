from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import joblib

from app.core.settings import settings


@lru_cache(maxsize=1)
def _load_bundle() -> Dict[str, object]:
    model_path = Path(settings.classifier_model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model classifier belum tersedia di {model_path}. Jalankan scripts/train_classifier.py terlebih dahulu."
        )
    return joblib.load(model_path)


def _build_features(ratios: Dict[str, float], feature_columns: List[str]) -> List[float]:
    values: List[float] = []
    for col in feature_columns:
        if col.startswith("ratio_"):
            key = col.replace("ratio_", "")
            values.append(float(ratios.get(key, 0.0)))
        else:
            values.append(float(ratios.get(col, 0.0)))
    return values


def predict_score(ratios: Dict[str, float]) -> float:
    bundle = _load_bundle()
    model = bundle.get("model")
    feature_columns = bundle.get("features", [])
    if model is None or not feature_columns:
        raise RuntimeError("Model classifier tidak valid. Jalankan ulang proses training.")
    row = _build_features(ratios, list(feature_columns))
    score = model.predict([row])[0]
    return float(score)
