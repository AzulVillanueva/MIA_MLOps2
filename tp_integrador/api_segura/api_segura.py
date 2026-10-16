"""API REST segura de stroke (TP1 + TP7): sirve el modelo CHAMPION de MLflow con JWT, roles y auditoria.

Es la capa de serving del TP integrador. Por defecto carga el champion desde MLflow (el que Airflow
reentrena y promueve), asi que requiere el stack Docker arriba (MLflow :5000, MinIO :9000).
Con MODEL_SOURCE=local usa en cambio el modelo entrenado en common/ (sin stack, para los mini-TPs).

    tp_integrador/servir.bat                                     (puerto 8009, champion)
    python -m uvicorn tp_integrador.api_segura.api_segura:app --port 8009
    set MODEL_SOURCE=local&& ... --port 8007                        (modelo local, desde MLOPs2_UBA_Tps/)
    Swagger: http://localhost:8009/docs  ->  boton "Authorize" con usuario/clave.

Usuarios de demo (en produccion vendrian de un proveedor de identidad, no del codigo):
    analista / analista123   -> puede predecir
    admin    / admin123      -> puede predecir, ver auditoria y model card
    invitado / invitado123   -> autentica pero NO tiene rol permitido (403)

Controles: JWT con expiracion, roles, validacion Pydantic, rate limiting (en memoria, o en Redis
con REDIS_URL), auditoria por hash, model card.
"""
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))
if os.environ.get("MODEL_SOURCE") == "local":
    # Modelo entrenado en common/ (mini-TPs); no requiere el stack Docker.
    from common.inference import load_model  # noqa: E402
else:
    # Por defecto: champion de MLflow (el mismo que sirve el stack Docker); requiere el stack arriba.
    from common.mlflow_champion import load_model  # noqa: E402

JWT_SECRET = os.environ.get("JWT_SECRET", "cambiar-en-produccion-con-32-bytes-o-mas")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "5"))  # consultas por ventana
RATE_WINDOW = 60  # segundos
AUDIT_LOG = Path(__file__).resolve().parent / "auditoria.jsonl"

# usuario -> (clave, rol). Solo para la demo.
USUARIOS = {
    "analista": ("analista123", "analista"),
    "admin": ("admin123", "admin"),
    "invitado": ("invitado123", "invitado"),
}

app = FastAPI(title="Stroke Predictor API (segura) - TP7", version="1.0.0")
model_wrapper = load_model()
oauth2 = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)
_hits: dict[str, list[float]] = {}


def _ahora() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def crear_token(usuario: str, rol: str, minutos: int = 15) -> str:
    payload = {"sub": usuario, "rol": rol, "exp": _ahora() + datetime.timedelta(minutes=minutos)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def usuario_autenticado(token: str = Depends(oauth2)) -> dict:
    """401 si falta, expiro o fue manipulado el token."""
    if not token:
        raise HTTPException(401, "falta token: usar /login o el boton Authorize")
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "token invalido o expirado")


def requiere_rol(*roles: str):
    """403 si el rol del token no esta entre los permitidos."""

    def dep(datos: dict = Depends(usuario_autenticado)) -> str:
        if datos.get("rol") not in roles:
            raise HTTPException(403, f"rol '{datos.get('rol')}' sin permiso (se requiere: {', '.join(roles)})")
        return datos["sub"]

    return dep


def _conectar_redis():
    """Si REDIS_URL esta definida, el contador se comparte entre procesos/instancias; si no, es en memoria."""
    url = os.environ.get("REDIS_URL")
    if not url:
        return None
    import redis

    cliente = redis.Redis.from_url(url, decode_responses=True)
    cliente.ping()
    return cliente


_redis = _conectar_redis()


def rate_limit(usuario: str = Depends(requiere_rol("analista", "admin"))) -> str:
    """429 si el usuario supera RATE_LIMIT consultas por ventana: frena el scraping / robo del modelo.

    Con REDIS_URL el contador vive en Redis (ventana fija con INCR + EXPIRE): vale para todas las
    instancias detras de un balanceador. Sin Redis, el contador es local a este proceso.
    """
    if _redis is not None:
        clave = f"ratelimit:{usuario}"
        n = _redis.incr(clave)
        if n == 1:
            _redis.expire(clave, RATE_WINDOW)
        if n > RATE_LIMIT:
            raise HTTPException(429, f"demasiadas solicitudes (max {RATE_LIMIT} por {RATE_WINDOW}s, contador compartido en Redis)")
        return usuario

    now = time.time()
    ventana = _hits.setdefault(usuario, [])
    ventana[:] = [t for t in ventana if now - t < RATE_WINDOW]
    if len(ventana) >= RATE_LIMIT:
        raise HTTPException(429, f"demasiadas solicitudes (max {RATE_LIMIT} por {RATE_WINDOW}s)")
    ventana.append(now)
    return usuario


def auditar(usuario: str, entrada: dict, prediccion: bool, probabilidad: float) -> None:
    registro = {
        "ts": _ahora().isoformat(),
        "usuario": usuario,
        # se guarda el hash, no el dato clinico del paciente
        "hash_entrada": hashlib.sha256(json.dumps(entrada, sort_keys=True).encode()).hexdigest(),
        "prediccion": prediccion,
        "probabilidad": round(probabilidad, 4),
        "modelo_version": model_wrapper.version,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")


class StrokeFeatures(BaseModel):
    gender: Literal["Male", "Female", "Other"]
    age: float = Field(ge=0, le=120)
    hypertension: int = Field(ge=0, le=1)
    heart_disease: int = Field(ge=0, le=1)
    ever_married: Literal["Yes", "No"]
    work_type: Literal["Private", "Self-employed", "Govt_job", "children", "Never_worked"]
    Residence_type: Literal["Urban", "Rural"]
    avg_glucose_level: float = Field(ge=0, le=350)
    bmi: float = Field(ge=0, le=100)
    smoking_status: Literal["formerly smoked", "never smoked", "smokes", "Unknown"]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gender": "Male", "age": 67, "hypertension": 0, "heart_disease": 1, "ever_married": "Yes",
                    "work_type": "Private", "Residence_type": "Urban", "avg_glucose_level": 228.69,
                    "bmi": 36.6, "smoking_status": "smokes",
                }
            ]
        }
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_name": model_wrapper.name, "model_version": model_wrapper.version}


@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Devuelve un JWT (15 min). En la demo, los usuarios estan en el codigo."""
    registro = USUARIOS.get(form.username)
    if registro is None or registro[0] != form.password:
        raise HTTPException(401, "usuario o clave incorrectos")
    return {"access_token": crear_token(form.username, registro[1]), "token_type": "bearer"}


@app.post("/v1/predict")
def predict(features: StrokeFeatures, usuario: str = Depends(rate_limit)):
    entrada = features.model_dump()
    stroke, label, proba = model_wrapper.predict_one(entrada)
    auditar(usuario, entrada, stroke, proba)
    return {
        "stroke_predicted": stroke,
        "label": label,
        "probability": proba,
        "model_name": model_wrapper.name,
        "model_version": model_wrapper.version,
    }


@app.get("/v1/model-card")
def model_card(_: str = Depends(requiere_rol("analista", "admin"))):
    """Model card (gobernanza): que es, para que sirve y sus limites."""
    return {
        "nombre": model_wrapper.name,
        "version": model_wrapper.version,
        "tipo": model_wrapper.data_dict["model_type"],
        "metricas": model_wrapper.metrics,
        "uso_previsto": "Apoyo a la priorizacion de pacientes con riesgo de stroke; no es diagnostico.",
        "limitaciones": "Dataset de Kaggle (~5k registros, clase positiva ~5%, balanceada con SMOTE).",
        "controles": ["JWT + roles", "validacion Pydantic", "rate limiting", "auditoria por hash"],
    }


@app.get("/v1/auditoria")
def auditoria(ultimos: int = 10, _: str = Depends(requiere_rol("admin"))):
    """Ultimas entradas del log de auditoria. Solo admin."""
    if not AUDIT_LOG.exists():
        return []
    lineas = AUDIT_LOG.read_text(encoding="utf-8").splitlines()[-ultimos:]
    return [json.loads(x) for x in lineas]
