"""Mini-TP 2 (Sesion 2): metadatos del modelo de stroke expuestos por GraphQL.

Expone el mismo modelo del Mini-TP 1 (REST) a traves de un esquema GraphQL
(Strawberry) con un tipo `Model` (name, version, metrics), para poder
comparar ambos protocolos leyendo la misma informacion.
"""
import sys
from pathlib import Path

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))
from common.inference import load_model  # noqa: E402

model_wrapper = load_model()


@strawberry.type
class Metrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    train_observations: int
    test_observations: int


@strawberry.type
class Model:
    name: str
    version: int
    model_type: str

    @strawberry.field
    def metrics(self) -> Metrics:
        m = model_wrapper.metrics
        return Metrics(
            accuracy=m["accuracy"],
            precision=m["precision"],
            recall=m["recall"],
            f1_score=m["f1_score"],
            train_observations=m["train_observations"],
            test_observations=m["test_observations"],
        )


@strawberry.type
class Query:
    @strawberry.field
    def model(self) -> Model:
        return Model(
            name=model_wrapper.name,
            version=model_wrapper.version,
            model_type=model_wrapper.data_dict["model_type"],
        )


schema = strawberry.Schema(query=Query)
app = FastAPI(title="Mini-TP 2 - metadatos del modelo por GraphQL")
app.include_router(GraphQLRouter(schema), prefix="/graphql")
