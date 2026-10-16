"""Standalone training script for the Stroke Prediction model.

Replica localmente (sin Airflow/MLflow/S3) el mismo pipeline del TP final de
Aprendizaje de Maquina II: limpieza, one-hot encoding, balanceo con SMOTE,
escalado estandar y un RandomForestClassifier. Guarda los artefactos que
consumen los tres mini-TP (REST, GraphQL, gRPC) en common/artifacts/.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "data" / "healthcare-dataset-stroke-data.csv"
ARTIFACTS_DIR = HERE / "artifacts"

TARGET_COL = "stroke"
TO_DROP_MAP = {
    "gender": "Other",
    "ever_married": "No",
    "work_type": "children",
    "Residence_type": "Rural",
    "smoking_status": "Unknown",
}
NON_CATEGORICAL_COLUMNS = ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"]
MODEL_PARAMS = {"n_estimators": 20, "criterion": "log_loss", "max_depth": 50, "random_state": 42}


def one_hot_encode(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Aplica one-hot encoding a las columnas categoricas, igual que el ETL de Airflow."""
    df = df.copy()
    encoded_columns: list[str] = []
    for label, to_drop in TO_DROP_MAP.items():
        unique_values = df[label].unique()
        prefix = "is" if len(unique_values) > 2 else label
        one_hot = pd.get_dummies(data=df[label], prefix=prefix)
        drop_col = f"{prefix}_{to_drop}"
        if drop_col in one_hot:
            one_hot = one_hot.drop(columns=drop_col)
        df = df.drop(columns=label).join(one_hot)
        encoded_columns.extend(one_hot.columns.tolist())
    return df, encoded_columns


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_CSV)
    if "id" in df.columns:
        df = df.set_index("id")
    df = df.drop_duplicates().dropna(subset=[c for c in df.columns if c != "bmi"])
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    df_dummies, categorical_columns = one_hot_encode(df)
    columns_after_dummy = df_dummies.drop(columns=TARGET_COL).columns.tolist()

    X = df_dummies.drop(columns=TARGET_COL)
    y = df_dummies[TARGET_COL]

    X_res, y_res = SMOTE(sampling_strategy="minority", random_state=42).fit_resample(X, y)
    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, stratify=y_res, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

    model = RandomForestClassifier(**MODEL_PARAMS)
    model.fit(X_train_scaled, y_train.to_numpy().ravel())
    y_pred = model.predict(X_test_scaled)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "train_observations": int(len(X_train)),
        "test_observations": int(len(X_test)),
    }

    model_name = "stroke_prediction_model_prod"
    model_version = 1

    joblib.dump(model, ARTIFACTS_DIR / "model.pkl")

    data_dict = {
        "model_name": model_name,
        "model_version": model_version,
        "model_type": type(model).__name__,
        "model_params": MODEL_PARAMS,
        "categorical_columns": categorical_columns,
        "columns_after_dummy": columns_after_dummy,
        "non_categorical_columns": NON_CATEGORICAL_COLUMNS,
        "to_drop_map": TO_DROP_MAP,
        "target_col": TARGET_COL,
        "standard_scaler_mean": scaler.mean_.tolist(),
        "standard_scaler_std": scaler.scale_.tolist(),
        "metrics": metrics,
    }
    with open(ARTIFACTS_DIR / "data_dict.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2)

    print(f"Modelo entrenado: {model_name} v{model_version}")
    print(json.dumps(metrics, indent=2))
    print(f"Artefactos guardados en {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
