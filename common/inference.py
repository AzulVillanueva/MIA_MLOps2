"""Carga de artefactos y logica de inferencia compartida por REST, GraphQL y gRPC.

Un solo lugar para no duplicar el preprocesamiento (one-hot + escalado) entre
los tres mini-TP: cada uno solo se ocupa del transporte (HTTP/GraphQL/gRPC).
"""
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ARTIFACTS_DIR = HERE / "artifacts"

FEATURE_FIELDS = [
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "ever_married",
    "work_type",
    "Residence_type",
    "avg_glucose_level",
    "bmi",
    "smoking_status",
]


@dataclass
class StrokeModel:
    model: object
    data_dict: dict

    @property
    def name(self) -> str:
        return self.data_dict["model_name"]

    @property
    def version(self) -> int:
        return self.data_dict["model_version"]

    @property
    def metrics(self) -> dict:
        return self.data_dict["metrics"]

    def predict_one(self, features: dict) -> tuple[bool, str, float]:
        return self.predict_batch([features])[0]

    def predict_batch(self, features_list: list[dict]) -> list[tuple[bool, str, float]]:
        df = pd.DataFrame(features_list, columns=FEATURE_FIELDS)
        encoded = _apply_one_hot_encoding(
            df,
            self.data_dict["categorical_columns"],
            self.data_dict["to_drop_map"],
            self.data_dict["non_categorical_columns"],
        ).astype(float)
        encoded = encoded[self.data_dict["columns_after_dummy"]]

        mean = np.array(self.data_dict["standard_scaler_mean"])
        std = np.array(self.data_dict["standard_scaler_std"])
        scaled = (encoded - mean) / std

        probabilities = self.model.predict_proba(scaled)[:, 1]
        predictions = self.model.predict(scaled)

        results = []
        for pred, proba in zip(predictions, probabilities):
            label = "Likely to have a stroke" if pred > 0.5 else "Not likely to have a stroke"
            results.append((bool(pred), label, float(proba)))
        return results


def _apply_one_hot_encoding(df_new, encoded_columns, to_drop_map, non_categorical_columns):
    """Misma logica que tp_integrador/stack/docker/fastapi/app.py para ser consistentes."""
    df_new = df_new.copy()
    non_categorical_data = df_new[non_categorical_columns]

    for label, to_drop in to_drop_map.items():
        prefix = "is" if len(to_drop_map) > 2 else label
        one_hot = pd.get_dummies(data=df_new[label], prefix=prefix)
        drop_col = f"{prefix}_{to_drop}"
        if drop_col in one_hot:
            one_hot = one_hot.drop(columns=drop_col)
        df_new = df_new.drop(columns=label).join(one_hot)

    for col in encoded_columns:
        if col not in df_new.columns:
            df_new[col] = 0

    df_new = df_new[encoded_columns]
    return pd.concat([non_categorical_data.reset_index(drop=True), df_new.reset_index(drop=True)], axis=1)


def load_model() -> StrokeModel:
    model = joblib.load(ARTIFACTS_DIR / "model.pkl")
    with open(ARTIFACTS_DIR / "data_dict.json", "r", encoding="utf-8") as f:
        data_dict = json.load(f)
    return StrokeModel(model=model, data_dict=data_dict)
