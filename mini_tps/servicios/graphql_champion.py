"""GraphQL del Mini-TP 2 sirviendo el modelo CHAMPION de MLflow (sin modificar mini_tps/tp2_graphql).

    .venv\\Scripts\\python.exe -m uvicorn mini_tps.servicios.graphql_champion:app --port 8012
"""
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))

import common.inference as _ci  # noqa: E402
from common import mlflow_champion  # noqa: E402

_ci.load_model = mlflow_champion.load_model  # el server original hace `from common.inference import load_model`

from mini_tps.tp2_graphql.server import app  # noqa: E402,F401
