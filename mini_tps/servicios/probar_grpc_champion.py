"""Cliente de prueba para el gRPC del champion (puerto 50052): unary + streaming."""
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT / "mini_tps" / "tp3_grpc"))

import grpc  # noqa: E402
import scoring_pb2  # noqa: E402
import scoring_pb2_grpc  # noqa: E402

CASO = dict(gender="Male", age=67, hypertension=0, heart_disease=1, ever_married="Yes", work_type="Private",
            residence_type="Urban", avg_glucose_level=228.69, bmi=36.6, smoking_status="smokes")

stub = scoring_pb2_grpc.ScoringStub(grpc.insecure_channel("localhost:50052"))
print("--- Predict (unary) ---")
print(stub.Predict(scoring_pb2.StrokeFeatures(**CASO)))
print("--- PredictBatch (streaming) ---")
casos = [scoring_pb2.StrokeFeatures(**CASO), scoring_pb2.StrokeFeatures(**{**CASO, "age": 25, "heart_disease": 0, "avg_glucose_level": 90.0})]
for r in stub.PredictBatch(scoring_pb2.StrokeBatch(items=casos)):
    print(r.label, "| probabilidad:", round(r.probability, 3))
