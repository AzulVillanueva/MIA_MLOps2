"""Mini-TP 1 (Sesion 1): API REST productiva para el modelo de prediccion de stroke.

Cumple la consigna: contrato Pydantic con las features reales del modelo,
POST /v1/predict, GET /health, y la respuesta incluye la version del modelo.
"""
import sys
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))
from common.inference import load_model  # noqa: E402

app = FastAPI(title="Stroke Predictor API", version="1.0.0")
model_wrapper = load_model()
START_TIME = time.time()


class StrokeFeatures(BaseModel):
    """Features reales del modelo de prediccion de stroke (dataset de Kaggle)."""

    gender: Literal["Male", "Female", "Other"] = Field(description="Genero del paciente")
    age: float = Field(description="Edad del paciente", ge=0, le=120)
    hypertension: int = Field(description="1 si el paciente tiene hipertension", ge=0, le=1)
    heart_disease: int = Field(description="1 si el paciente tiene una enfermedad cardiaca", ge=0, le=1)
    ever_married: Literal["Yes", "No"] = Field(description="Si el paciente estuvo casado alguna vez")
    work_type: Literal["Private", "Self-employed", "Govt_job", "children", "Never_worked"] = Field(
        description="Tipo de trabajo del paciente"
    )
    Residence_type: Literal["Urban", "Rural"] = Field(description="Tipo de residencia del paciente")
    avg_glucose_level: float = Field(description="Nivel promedio de glucosa en sangre", ge=0, le=350)
    bmi: float = Field(description="Indice de masa corporal", ge=0, le=100)
    smoking_status: Literal["formerly smoked", "never smoked", "smokes", "Unknown"] = Field(
        description="Estado de fumador del paciente"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gender": "Male",
                    "age": 67,
                    "hypertension": 0,
                    "heart_disease": 1,
                    "ever_married": "Yes",
                    "work_type": "Private",
                    "Residence_type": "Urban",
                    "avg_glucose_level": 228.69,
                    "bmi": 36.6,
                    "smoking_status": "smokes",
                }
            ]
        }
    }


class PredictionResponse(BaseModel):
    stroke_predicted: bool = Field(description="True si el modelo predice riesgo de stroke")
    label: Literal["Not likely to have a stroke", "Likely to have a stroke"]
    probability: float = Field(description="Probabilidad estimada de stroke", ge=0, le=1)
    model_name: str
    model_version: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_name: str
    model_version: int
    uptime_seconds: float


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    train_observations: int
    test_observations: int


class ModelInfoResponse(BaseModel):
    """Metadatos completos del modelo (equivalente REST del tipo `Model` de GraphQL).

    Se usa para comparar REST vs GraphQL: aqui siempre viajan todos los campos,
    aunque el cliente solo necesite uno (over-fetching).
    """

    name: str
    version: int
    model_type: str
    metrics: ModelMetrics


@app.get("/v1/model", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(
        name=model_wrapper.name,
        version=model_wrapper.version,
        model_type=model_wrapper.data_dict["model_type"],
        metrics=ModelMetrics(**model_wrapper.metrics),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_name=model_wrapper.name,
        model_version=model_wrapper.version,
        uptime_seconds=time.time() - START_TIME,
    )


@app.post("/v1/predict", response_model=PredictionResponse)
def predict(features: StrokeFeatures) -> PredictionResponse:
    stroke_predicted, label, probability = model_wrapper.predict_one(features.model_dump())
    return PredictionResponse(
        stroke_predicted=stroke_predicted,
        label=label,
        probability=probability,
        model_name=model_wrapper.name,
        model_version=model_wrapper.version,
    )
