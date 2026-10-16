"""Cliente gRPC del Mini-TP 3: llamada unary y server-streaming."""
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoring_pb2  # noqa: E402
import scoring_pb2_grpc  # noqa: E402

VALID_CASE = dict(
    gender="Male",
    age=67,
    hypertension=0,
    heart_disease=1,
    ever_married="Yes",
    work_type="Private",
    residence_type="Urban",
    avg_glucose_level=228.69,
    bmi=36.6,
    smoking_status="smokes",
)

BATCH = [
    VALID_CASE,
    dict(VALID_CASE, age=30, hypertension=0, heart_disease=0, avg_glucose_level=90.0, bmi=22.0, smoking_status="never smoked"),
    dict(VALID_CASE, age=80, hypertension=1, heart_disease=1, avg_glucose_level=250.0, bmi=40.0),
]


def main() -> None:
    channel = grpc.insecure_channel("localhost:50051")
    stub = scoring_pb2_grpc.ScoringStub(channel)

    print("--- Predict (unary) ---")
    response = stub.Predict(scoring_pb2.StrokeFeatures(**VALID_CASE))
    print(response)

    print("--- PredictBatch (server-streaming) ---")
    batch = scoring_pb2.StrokeBatch(items=[scoring_pb2.StrokeFeatures(**item) for item in BATCH])
    for prediction in stub.PredictBatch(batch):
        print(prediction.label, "| probabilidad:", round(prediction.probability, 3))

    channel.close()


if __name__ == "__main__":
    main()
