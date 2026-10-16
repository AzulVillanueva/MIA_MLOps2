"""Registra el modelo inicial (champion) en MLflow. Es el paso previo que exige el DAG de reentrenamiento.
Se puede volver a correr: registra una version nueva y mueve el alias champion a ella.

Equivale a notebook/mlflow_model.ipynb, pero ejecutable dentro del contenedor de Airflow:
    docker exec -i airflow_scheduler python - < airflow/register_champion.py
Requiere que el DAG process_etl_stroke_prediction ya haya corrido (genera los CSV en s3://data/final/).
"""
import datetime

import awswrangler as wr
import mlflow
import mlflow.models
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

mlflow.set_tracking_uri("http://mlflow:5000")

P = "healthcare-dataset-stroke-data_"
X_train = wr.s3.read_csv(f"s3://data/final/train/{P}X_train.csv")
y_train = wr.s3.read_csv(f"s3://data/final/train/{P}y_train.csv")
X_test = wr.s3.read_csv(f"s3://data/final/test/{P}X_test.csv")
y_test = wr.s3.read_csv(f"s3://data/final/test/{P}y_test.csv")

experiment = mlflow.get_experiment_by_name("Stroke Prediction")
experiment_id = experiment.experiment_id if experiment else mlflow.create_experiment("Stroke Prediction")

params = {"n_estimators": 20, "criterion": "log_loss", "max_depth": 50}
model = RandomForestClassifier(**params).fit(X_train, y_train.to_numpy().ravel())
f1 = f1_score(y_test, model.predict(X_test))
print("f1 score:", f1)

with mlflow.start_run(experiment_id=experiment_id, run_name="stroke_prediction_train_" + datetime.datetime.today().strftime("%Y/%m/%d-%H:%M:%S")):
    mlflow.set_tags({"project": "Stroke Prediction", "model_family": "sklearn", "feature_set_version": 1})
    mlflow.log_params(params)
    mlflow.log_metric("f1_score", f1)
    signature = mlflow.models.infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        signature=signature,
        serialization_format="cloudpickle",
        registered_model_name="stroke_prediction_model_dev",
        metadata={"model_data_version": 1},
    )
    model_uri = mlflow.get_artifact_uri("model")

client = mlflow.MlflowClient()
name = "stroke_prediction_model_prod"
try:
    client.get_registered_model(name)
except mlflow.exceptions.MlflowException:  # primera vez: el modelo todavia no existe
    client.create_registered_model(
        name=name,
        description="Predice si un paciente es probable que tenga un stroke segun sus parametros.",
    )
# Si ya existia, se registra una version nueva y el alias champion pasa a ella (las anteriores se conservan).
tags = model.get_params()
tags["model"] = type(model).__name__
tags["f1-score"] = f1
result = client.create_model_version(name=name, source=model_uri, run_id=model_uri.split("/")[-3], tags=tags)
client.set_registered_model_alias(name, "champion", result.version)
print("champion registrado: version", result.version)
