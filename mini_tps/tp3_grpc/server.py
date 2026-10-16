"""Mini-TP 3 (Sesion 3): servidor gRPC para el modelo de prediccion de stroke.

Carga el modelo una sola vez (al importar el modulo) y expone Predict (unary)
y PredictBatch (server-streaming), reusando la misma logica de inferencia
que el Mini-TP 1 (REST) y el Mini-TP 2 (GraphQL).
"""
import sys
from concurrent import futures
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))

import scoring_pb2  # noqa: E402
import scoring_pb2_grpc  # noqa: E402
from common.inference import load_model  # noqa: E402

model_wrapper = load_model()


def _features_to_dict(features: "scoring_pb2.StrokeFeatures") -> dict:
    return {
        "gender": features.gender,
        "age": features.age,
        "hypertension": features.hypertension,
        "heart_disease": features.heart_disease,
        "ever_married": features.ever_married,
        "work_type": features.work_type,
        "Residence_type": features.residence_type,
        "avg_glucose_level": features.avg_glucose_level,
        "bmi": features.bmi,
        "smoking_status": features.smoking_status,
    }


def _to_prediction(stroke_predicted: bool, label: str, probability: float) -> "scoring_pb2.Prediction":
    return scoring_pb2.Prediction(
        stroke_predicted=stroke_predicted,
        label=label,
        probability=probability,
        model_name=model_wrapper.name,
        model_version=model_wrapper.version,
    )


class ScoringServicer(scoring_pb2_grpc.ScoringServicer):
    def Predict(self, request, context):
        stroke_predicted, label, probability = model_wrapper.predict_one(_features_to_dict(request))
        return _to_prediction(stroke_predicted, label, probability)

    def PredictBatch(self, request, context):
        features_list = [_features_to_dict(item) for item in request.items]
        for stroke_predicted, label, probability in model_wrapper.predict_batch(features_list):
            yield _to_prediction(stroke_predicted, label, probability)


def serve(port: int = 50051) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    scoring_pb2_grpc.add_ScoringServicer_to_server(ScoringServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Servidor gRPC de Scoring en localhost:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
