"""Model training for Stroke Prediction with Apache Airflow DAG"""

import datetime

from airflow.decorators import task
from airflow import DAG

MARKDOWN_TEXT = """
### Re-Train the Model for Stroke Prediction

This DAG re-trains the model based on new data, tests the previous model, and put in production the new one 
if it performs  better than the old one. It uses the F1 score to evaluate the model with the test data.
"""

default_args = {
    "owner": "Grupo Aprendizaje de Máquina II",
    "depends_on_past": False,
    "schedule_interval": None,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
    "dagrun_timeout": datetime.timedelta(minutes=15),
}

DAG_DESCRIPTION = """\
Re-train the model based on new data, tests the previous model, \
and put in production the new one if it performs better than the old one
"""

# Initialize the DAG
with DAG(
    "retrain_stroke_prediction_model",
    description=DAG_DESCRIPTION,
    default_args=default_args,
    schedule_interval=None,  # No automatic scheduling
    start_date=datetime.datetime(2024, 12, 1),
    tags=["Training", "Stroke Prediction"],
    doc_md=MARKDOWN_TEXT,
    catchup=False,
) as dag:

    @task.virtualenv(
        task_id="train_the_challenger_model",
        requirements=["scikit-learn", "mlflow", "awswrangler"],
        system_site_packages=True,
    )
    def train_the_challenger_model():
        """Train new model to challenge champion"""
        import datetime
        import mlflow
        import awswrangler as wr
        from sklearn.base import clone
        from sklearn.metrics import f1_score

        mlflow.set_tracking_uri("http://mlflow:5000")

        def load_champion_model():
            """Load the best model in production"""
            model_name = "stroke_prediction_model_prod"
            alias = "champion"
            client = mlflow.MlflowClient()
            model_data = client.get_model_version_by_alias(model_name, alias)
            champion_version = mlflow.sklearn.load_model(model_data.source)
            return champion_version

        def load_train_test_data():
            """Load data for training and testing of a new model"""
            PREFIX_CSV_FILES = "healthcare-dataset-stroke-data_"
            X_train = wr.s3.read_csv(f"s3://data/final/train/{PREFIX_CSV_FILES}X_train.csv")
            y_train = wr.s3.read_csv(f"s3://data/final/train/{PREFIX_CSV_FILES}y_train.csv")
            X_test = wr.s3.read_csv(f"s3://data/final/test/{PREFIX_CSV_FILES}X_test.csv")
            y_test = wr.s3.read_csv(f"s3://data/final/test/{PREFIX_CSV_FILES}y_test.csv")
            return X_train, y_train, X_test, y_test

        def mlflow_track_experiment(model, X):
            """Setup MLflow experiment"""
            experiment = mlflow.set_experiment("Stroke Prediction")
            mlflow.start_run(
                run_name="challenger_run_" + datetime.datetime.today().strftime('%Y/%m/%d-%H:%M:%S"'),
                experiment_id=experiment.experiment_id,
                tags={"experiment": "challenger models", "dataset": "Stroke prediction"},
                log_system_metrics=True,
            )
            params = model.get_params()
            params["model"] = type(model).__name__
            mlflow.log_params(params)
            signature = mlflow.models.infer_signature(X, model.predict(X))
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=signature,
                serialization_format="cloudpickle",
                registered_model_name="stroke_prediction_model_dev",
                metadata={"model_data_version": 1},
            )
            return mlflow.get_artifact_uri("model")

        def register_challenger(model, f1_score, model_uri):
            """Register new model in MLflow environment"""
            client = mlflow.MlflowClient()
            name = "stroke_prediction_model_prod"
            tags = model.get_params()
            tags["model"] = type(model).__name__
            tags["f1-score"] = f1_score
            result = client.create_model_version(
                name=name, source=model_uri, run_id=model_uri.split("/")[-3], tags=tags
            )
            client.set_registered_model_alias(name, "challenger", result.version)

        champion_model = load_champion_model()
        challenger_model = clone(champion_model)

        # train, test, score
        X_train, y_train, X_test, y_test = load_train_test_data()
        challenger_model.fit(X_train, y_train.to_numpy().ravel())
        y_pred = challenger_model.predict(X_test)
        f1_score = f1_score(y_test.to_numpy().ravel(), y_pred)

        artifact_uri = mlflow_track_experiment(challenger_model, X_train)
        register_challenger(challenger_model, f1_score, artifact_uri)

    @task.virtualenv(
        task_id="evaluate_champion_challenge",
        requirements=["scikit-learn", "mlflow", "awswrangler"],
        system_site_packages=True,
    )
    def evaluate_champion_challenge():
        import mlflow
        import awswrangler as wr
        from sklearn.metrics import f1_score

        mlflow.set_tracking_uri("http://mlflow:5000")

        def load_the_model(alias):
            model_name = "stroke_prediction_model_prod"
            client = mlflow.MlflowClient()
            model_data = client.get_model_version_by_alias(model_name, alias)
            model = mlflow.sklearn.load_model(model_data.source)
            return model

        def load_the_test_data():
            PREFIX_CSV_FILES = "healthcare-dataset-stroke-data_"
            X_test = wr.s3.read_csv(f"s3://data/final/test/{PREFIX_CSV_FILES}X_test.csv")
            y_test = wr.s3.read_csv(f"s3://data/final/test/{PREFIX_CSV_FILES}y_test.csv")
            return X_test, y_test

        def promote_challenger(name):
            client = mlflow.MlflowClient()
            # Demote the champion
            client.delete_registered_model_alias(name, "champion")
            # Load the challenger from registry
            challenger_version = client.get_model_version_by_alias(name, "challenger")
            # delete the alias of challenger
            client.delete_registered_model_alias(name, "challenger")
            # Transform in champion
            client.set_registered_model_alias(name, "champion", challenger_version.version)

        def demote_challenger(name):
            client = mlflow.MlflowClient()
            # delete the alias of challenger
            client.delete_registered_model_alias(name, "challenger")

        # Load the champion model
        champion_model = load_the_model("champion")

        # Load the challenger model
        challenger_model = load_the_model("challenger")

        # Load the dataset
        X_test, y_test = load_the_test_data()

        # Obtain the metric of the models
        y_pred_champion = champion_model.predict(X_test)
        f1_score_champion = f1_score(y_test.to_numpy().ravel(), y_pred_champion)

        y_pred_challenger = challenger_model.predict(X_test)
        f1_score_challenger = f1_score(y_test.to_numpy().ravel(), y_pred_challenger)

        experiment = mlflow.set_experiment("Stroke Prediction")

        # Obtain the last experiment run_id to log the new information
        list_run = mlflow.search_runs([experiment.experiment_id], output_format="list")

        with mlflow.start_run(run_id=list_run[0].info.run_id):
            mlflow.log_metric("test_f1_challenger", f1_score_challenger)
            mlflow.log_metric("test_f1_champion", f1_score_champion)

            if f1_score_challenger > f1_score_champion:
                mlflow.log_param("Winner", "Challenger")
            else:
                mlflow.log_param("Winner", "Champion")

        name = "stroke_prediction_model_prod"
        if f1_score_challenger > f1_score_champion:
            promote_challenger(name)
        else:
            demote_challenger(name)

    train_the_challenger_model() >> evaluate_champion_challenge()
