# Mini-TP 6 — Modelo en el Data Lake (Sesión 6)

Sube el modelo de stroke a un Data Lake (MinIO, compatible S3) organizado en zonas con versión, y lo **sirve cargándolo desde el lake** en lugar de desde disco.

## Entregable

**[`mini_tp6_resuelto.ipynb`](mini_tp6_resuelto.ipynb)** — necesita MinIO corriendo en `localhost:9000`.

`mlflow_tp6.db` es la base SQLite del tracking de MLflow. **No está versionada**: se genera sola al correr el notebook (parte opcional de MLflow) y está en el `.gitignore`.

## Qué hace el notebook

1. **Configuración:** credenciales por variables de entorno (`minio` / `minio123`), endpoint `http://localhost:9000`, bucket `datalake-tp6`.
2. **Bucket y zonas:** crea `raw/`, `curated/` y `models/` (prefijos).
3. **Modelo y datos:** carga el modelo de `common/` y prepara el dataset crudo y el preprocesado.
4. **Subida al lake:** CSV a `raw/stroke/`, Parquet a `curated/stroke/`, modelo y metadata a `models/v1/`.
5. **Servir desde el lake:** `cargar_modelo_desde_lake()` descarga el modelo con `boto3` y predice sobre un registro crudo.
6. **(Opcional) MLflow:** registra el experimento con artefactos en `s3://datalake-tp6/mlflow`.
7. **Reflexión:** por qué servir desde el lake, versionado inmutable (`v1`, `v2`, rollback) y dónde guardar predicciones (`curated/predictions/`).

## Cómo correr

Levantar MinIO:

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minio -e MINIO_ROOT_PASSWORD=minio123 \
  quay.io/minio/minio server /data --console-address ":9001"
```

La consola web queda en http://localhost:9001. Luego:

```bash
python common/train_model.py     # solo la primera vez
```

Abrir el notebook con el kernel `mlops2` y ejecutar todas las celdas. Dependencias específicas: `boto3`, `pyarrow` (Parquet) y `mlflow`, todas en `requirements.txt`.
