import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.settings import settings


def train() -> None:
    dataset_dir = Path(settings.dataset_dir)
    dataset_path = dataset_dir / "processed" / "menu_classifier_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset belum ditemukan di {dataset_path}. Jalankan scripts/build_classifier_dataset.py terlebih dahulu."
        )

    df = pd.read_csv(dataset_path)
    feature_cols = [col for col in df.columns if col.startswith("ratio_")]
    if not feature_cols:
        raise RuntimeError("Kolom fitur tidak ditemukan di dataset.")

    X = df[feature_cols]
    y = df["score"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    artifacts_dir = Path(settings.classifier_model_path).parent
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    bundle = {"model": model, "features": feature_cols}
    joblib.dump(bundle, settings.classifier_model_path)

    print(f"Model tersimpan di {settings.classifier_model_path}")
    print(f"MAE: {mae:.4f}")


if __name__ == "__main__":
    train()
