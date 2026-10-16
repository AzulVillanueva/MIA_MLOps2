"""Compara la latencia de gRPC (unary) vs REST (/v1/predict) para la misma prediccion.

Requiere el servidor gRPC (mini_tps/tp3_grpc/server.py, puerto 50051) y el REST
del Mini-TP 1 (mini_tps/tp1_rest/api.py, puerto 8001) corriendo.
"""
import sys
import time
from pathlib import Path

import grpc
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoring_pb2  # noqa: E402
import scoring_pb2_grpc  # noqa: E402

N = 200

GRPC_CASE = dict(
    gender="Male", age=67, hypertension=0, heart_disease=1, ever_married="Yes",
    work_type="Private", residence_type="Urban", avg_glucose_level=228.69,
    bmi=36.6, smoking_status="smokes",
)
REST_CASE = {**GRPC_CASE, "Residence_type": GRPC_CASE.pop("residence_type")}
REST_URL = "http://localhost:8001/v1/predict"


def measure_grpc() -> float:
    channel = grpc.insecure_channel("localhost:50051")
    stub = scoring_pb2_grpc.ScoringStub(channel)
    request = scoring_pb2.StrokeFeatures(**GRPC_CASE)

    stub.Predict(request)  # warm-up
    start = time.perf_counter()
    for _ in range(N):
        stub.Predict(request)
    elapsed = time.perf_counter() - start
    channel.close()
    return elapsed / N * 1000


def measure_rest() -> float:
    # Sesion con keep-alive: sin esto, cada llamada abre una conexion TCP
    # nueva y la comparacion queda dominada por el handshake, no por REST en si.
    with requests.Session() as session:
        session.post(REST_URL, json=REST_CASE)  # warm-up
        start = time.perf_counter()
        for _ in range(N):
            session.post(REST_URL, json=REST_CASE)
        elapsed = time.perf_counter() - start
    return elapsed / N * 1000


def main() -> None:
    grpc_ms = measure_grpc()
    rest_ms = measure_rest()
    print(f"gRPC: {grpc_ms:.3f} ms/llamada  (N={N})")
    print(f"REST: {rest_ms:.3f} ms/llamada  (N={N})")
    print(f"gRPC fue {rest_ms / grpc_ms:.2f}x mas rapido que REST en este caso.")


if __name__ == "__main__":
    main()
