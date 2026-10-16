"""Servidor gRPC del Mini-TP 3 sirviendo el modelo CHAMPION de MLflow (sin modificar mini_tps/tp3_grpc).

    .venv\\Scripts\\python.exe mini_tps\\servicios\\grpc_champion.py      (puerto 50052)
"""
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "mini_tps" / "tp3_grpc"))

import common.inference as _ci  # noqa: E402
from common import mlflow_champion  # noqa: E402

_ci.load_model = mlflow_champion.load_model

import server as grpc_server  # noqa: E402  (mini_tps/tp3_grpc/server.py)

if __name__ == "__main__":
    grpc_server.serve(50052)
