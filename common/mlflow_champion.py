"""Carga el modelo CHAMPION desde MLflow (el mismo que sirve el stack Docker) con la interfaz de common.inference.

Asi REST seguro, GraphQL y gRPC pueden consumir el champion que Airflow reentrena y promueve,
sin modificar el codigo de los mini-TPs: se reemplaza `load_model` antes de importarlos.

Requiere el stack Docker arriba (MLflow en :5000, MinIO en :9000).
"""
import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("AWS_ACCESS_KEY_ID", "minio")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minio123")
os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ENDPOINT_URL_S3", "http://localhost:9000")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
# Si MLflow no responde, fallar rapido en vez de colgarse reintentando.
TIMEOUT_S = 10
os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", str(TIMEOUT_S))
os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "0")

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))

import boto3  # noqa: E402
import mlflow  # noqa: E402
import pandas as pd  # noqa: E402
import requests  # noqa: E402
from botocore.config import Config  # noqa: E402
from botocore.exceptions import BotoCoreError  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score  # noqa: E402

from common.inference import StrokeModel  # noqa: E402

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = "stroke_prediction_model_prod"
ALIAS = "champion"

# Mismos valores que usa la API del stack (docker/fastapi/app.py)
TO_DROP_MAP = {
    "gender": "Other",
    "ever_married": "No",
    "work_type": "children",
    "Residence_type": "Rural",
    "smoking_status": "Unknown",
}
NON_CATEGORICAL = ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"]


def _s3_csv(s3, key: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(s3.get_object(Bucket="data", Key=key)["Body"].read()))


def _normalizar_arboles(model) -> None:
    """Corrige las probabilidades de un RandomForest guardado con scikit-learn < 1.4.

    Hasta la 1.3 los nodos guardaban CONTEOS de muestras; desde la 1.4 guardan PROPORCIONES. Cargar un
    pickle viejo en un scikit-learn nuevo deja `predict_proba` sin normalizar (sumas > 1) y puede alterar
    tambien la clase predicha. Se normalizan los nodos en memoria. Verificado: sin normalizar, el F1 del champion
    sobre test daba 0.953; normalizado da 0.972, que coincide con el que registra MLflow.
    """
    for arbol in getattr(model, "estimators_", []):
        v = arbol.tree_.value
        sumas = v.sum(axis=(1, 2), keepdims=True)
        if (sumas > 1.0 + 1e-6).any():
            v /= sumas


def _verificar_mlflow() -> None:
    """Corta con un mensaje claro si MLflow no responde (en vez de colgar el proceso)."""
    try:
        requests.get(f"{MLFLOW_URI}/health", timeout=TIMEOUT_S)
    except requests.exceptions.RequestException as e:
        destino = MLFLOW_URI.split("://", 1)[-1].rstrip("/")
        raise RuntimeError(
            f"No se pudo conectar a MLflow en {destino}. "
            "Levanta el stack (tp_integrador/stack) o usa MODEL_SOURCE=local."
        ) from e


def load_model() -> StrokeModel:
    import warnings

    _verificar_mlflow()
    mlflow.set_tracking_uri(MLFLOW_URI)
    mv = mlflow.MlflowClient().get_model_version_by_alias(MODEL_NAME, ALIAS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # el champion se entreno con otra version de scikit-learn
        model = mlflow.sklearn.load_model(mv.source)

    _normalizar_arboles(model)

    s3 = boto3.client(
        "s3", config=Config(connect_timeout=TIMEOUT_S, read_timeout=TIMEOUT_S, retries={"max_attempts": 1})
    )
    try:
        data_dict = json.loads(s3.get_object(Bucket="data", Key="data_info/data.json")["Body"].read().decode())
    except BotoCoreError as e:
        raise RuntimeError(
            f"No se pudo conectar a MinIO en {os.environ['AWS_ENDPOINT_URL_S3'].split('://', 1)[-1]}. "
            "Levanta el stack (tp_integrador/stack) o usa MODEL_SOURCE=local."
        ) from e

    # Metricas reales del champion sobre el conjunto de test que dejo el DAG ETL
    p = "final/{split}/healthcare-dataset-stroke-data_{xy}_{split}.csv"
    X_test = _s3_csv(s3, p.format(split="test", xy="X"))
    y_test = _s3_csv(s3, p.format(split="test", xy="y")).to_numpy().ravel()
    X_train = _s3_csv(s3, p.format(split="train", xy="X"))
    pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred)),
        "recall": float(recall_score(y_test, pred)),
        "f1_score": float(f1_score(y_test, pred)),
        "train_observations": int(len(X_train)),
        "test_observations": int(len(X_test)),
    }

    data_dict.update(
        to_drop_map=TO_DROP_MAP,
        non_categorical_columns=NON_CATEGORICAL,
        model_name=f"{MODEL_NAME} (champion MLflow)",
        model_version=int(mv.version),
        model_type=type(model).__name__,
        metrics=metrics,
    )
    print(f"[champion] version {mv.version} cargada desde MLflow | F1 en test = {metrics['f1_score']:.3f}", flush=True)
    return StrokeModel(model=model, data_dict=data_dict)
