"""Publica el modelo CHAMPION de MLflow en el Data Lake (MinIO) y lo sirve DESDE el lake.

Cierra el ciclo:  Airflow reentrena -> MLflow promueve el champion -> se publica en el lake (models/vN, inmutable)
-> un servicio lo descarga del lake, verifica su integridad (sha256) y predice.

    .venv\\Scripts\\python.exe tp_integrador\\datalake\\publicar_champion.py

Requiere el stack Docker arriba (MLflow :5000 y MinIO :9000). No modifica el notebook del Mini-TP 6: usa el mismo
bucket (datalake-tp6) y la misma convencion de zonas (models/vN/...), y agrega un puntero models/champion.json.
"""
import datetime
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
sys.path.insert(0, str(ROOT))

import boto3  # noqa: E402
import joblib  # noqa: E402
import mlflow  # noqa: E402
import sklearn  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402

from common.inference import StrokeModel  # noqa: E402
from common import mlflow_champion  # noqa: E402

BUCKET = "datalake-tp6"
CASO = {
    "gender": "Male", "age": 67, "hypertension": 0, "heart_disease": 1, "ever_married": "Yes",
    "work_type": "Private", "Residence_type": "Urban", "avg_glucose_level": 228.69,
    "bmi": 36.6, "smoking_status": "smokes",
}


def publicar(s3) -> StrokeModel:
    print("1) Cargando el champion desde MLflow...")
    champion = mlflow_champion.load_model()
    mv = mlflow.MlflowClient().get_model_version_by_alias(mlflow_champion.MODEL_NAME, mlflow_champion.ALIAS)
    v = int(mv.version)

    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        print(f"   bucket {BUCKET} creado")

    prefijo = f"models/v{v}"
    try:
        s3.head_object(Bucket=BUCKET, Key=f"{prefijo}/stroke_prediction_model.pkl")
        print(f"2) {prefijo}/ ya existe en el lake: las versiones son inmutables, no se sobrescribe.")
    except ClientError:
        buf = io.BytesIO()
        joblib.dump(champion.model, buf)
        blob = buf.getvalue()
        metadata = {
            "origen": "mlflow champion",
            "mlflow_model": mlflow_champion.MODEL_NAME,
            "mlflow_version": v,
            "mlflow_run_id": mv.run_id,
            "sha256": hashlib.sha256(blob).hexdigest(),
            "sklearn_version": sklearn.__version__,
            "metricas_test": champion.metrics,
            "publicado": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        s3.put_object(Bucket=BUCKET, Key=f"{prefijo}/stroke_prediction_model.pkl", Body=blob)
        s3.put_object(Bucket=BUCKET, Key=f"{prefijo}/data_dict.json", Body=json.dumps(champion.data_dict).encode())
        s3.put_object(Bucket=BUCKET, Key=f"{prefijo}/metadata.json", Body=json.dumps(metadata, indent=2).encode())
        print(f"2) Publicado s3://{BUCKET}/{prefijo}/ (modelo, data_dict, metadata con sha256)")

    s3.put_object(
        Bucket=BUCKET,
        Key="models/champion.json",
        Body=json.dumps({"version": v, "path": prefijo}).encode(),
    )
    print(f"   puntero actualizado: models/champion.json -> v{v}")
    return champion


def servir_desde_lake(s3, esperado: StrokeModel) -> None:
    print("3) Sirviendo DESDE el lake (sin MLflow)...")
    puntero = json.loads(s3.get_object(Bucket=BUCKET, Key="models/champion.json")["Body"].read())
    p = puntero["path"]
    get = lambda k: s3.get_object(Bucket=BUCKET, Key=f"{p}/{k}")["Body"].read()  # noqa: E731
    blob, meta = get("stroke_prediction_model.pkl"), json.loads(get("metadata.json"))
    sha = hashlib.sha256(blob).hexdigest()
    assert sha == meta["sha256"], "integridad rota: el sha256 del modelo no coincide con su metadata"
    print(f"   integridad OK (sha256 {sha[:12]}...) | origen: {meta['origen']} v{meta['mlflow_version']} | F1 test = {meta['metricas_test']['f1_score']:.3f}")

    modelo = StrokeModel(model=joblib.load(io.BytesIO(blob)), data_dict=json.loads(get("data_dict.json")))
    pred, label, proba = modelo.predict_one(CASO)
    pred_ref, _, proba_ref = esperado.predict_one(CASO)
    print(f"   prediccion desde el lake: {label} (p={proba:.3f})")
    assert (pred, round(proba, 6)) == (pred_ref, round(proba_ref, 6)), "el modelo del lake difiere del champion"
    print("   coincide con el champion de MLflow")
    print("\nObjetos del lake bajo models/:")
    for o in s3.list_objects_v2(Bucket=BUCKET, Prefix="models/").get("Contents", []):
        print(f"   s3://{BUCKET}/{o['Key']}  ({o['Size']} bytes)")


if __name__ == "__main__":
    s3 = boto3.client("s3")  # credenciales y endpoint los fija mlflow_champion (minio / localhost:9000)
    champion = publicar(s3)
    servir_desde_lake(s3, champion)
