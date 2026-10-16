"""REST-API for Stroke Prediction model"""
import json
import pickle
import boto3
import mlflow

import numpy as np
import pandas as pd

from typing import Literal
from fastapi import FastAPI, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing_extensions import Annotated


def apply_one_hot_encoding(df_new, encoded_columns, to_drop_map, non_categorical_columns):
    """Apply one hot encoding in categorical variables"""

    non_categorical_data = df_new[non_categorical_columns]

    # one-hot encoding
    for label, to_drop in to_drop_map.items():
        prefix = "is" if len(to_drop_map) > 2 else label
        one_hot = pd.get_dummies(data=df_new[label], prefix=prefix)
        if prefix + "_" + to_drop in one_hot:
            one_hot.drop(prefix + "_" + to_drop, axis=1, inplace=True)
        df_new.drop(label, axis=1, inplace=True)
        df_new = df_new.join(one_hot)

    # default
    for col in encoded_columns:
        if col not in df_new.columns:
            df_new[col] = 0

    # reorder
    df_new = df_new[encoded_columns]

    # join with non-categorical
    return pd.concat([non_categorical_data.reset_index(drop=True), df_new.reset_index(drop=True)], axis=1)


def load_model(model_name: str, alias: str):
    """
    Load a trained model and associated data dictionary.

    This function attempts to load a trained model specified by its name and alias. If the model is not found in the
    MLflow registry, it loads the default model from a file. Additionally, it loads information about the ETL pipeline
    from an S3 bucket. If the data dictionary is not found in the S3 bucket, it loads it from a local file.

    :param model_name: The name of the model.
    :param alias: The alias of the model version.
    :return: A tuple containing the loaded model, its version, and the data dictionary.
    """

    try:
        # Load the trained model from MLflow
        mlflow.set_tracking_uri('http://mlflow:5000')
        client_mlflow = mlflow.MlflowClient()

        model_data_mlflow = client_mlflow.get_model_version_by_alias(model_name, alias)
        model_ml = mlflow.sklearn.load_model(model_data_mlflow.source)
        version_model_ml = int(model_data_mlflow.version)
    except:
        # If there is no registry in MLflow, open the default model
        file_ml = open('/app/files/model.pkl', 'rb')
        model_ml = pickle.load(file_ml)
        file_ml.close()
        version_model_ml = 0

    try:
        # Load information of the ETL pipeline from S3
        s3 = boto3.client('s3')

        s3.head_object(Bucket='data', Key='data_info/data.json')
        result_s3 = s3.get_object(Bucket='data', Key='data_info/data.json')
        text_s3 = result_s3["Body"].read().decode()
        data_dictionary = json.loads(text_s3)

        data_dictionary["standard_scaler_mean"] = np.array(data_dictionary["standard_scaler_mean"])
        data_dictionary["standard_scaler_std"] = np.array(data_dictionary["standard_scaler_std"])
    except:
        # If data dictionary is not found in S3, load it from local file
        file_s3 = open("/app/files/data.json", "r")
        data_dictionary = json.load(file_s3)
        file_s3.close()

    return model_ml, version_model_ml, data_dictionary


def check_model():
    """
    Check for updates in the model and update if necessary.

    The function checks the model registry to see if the version of the champion model has changed. If the version
    has changed, it updates the model and the data dictionary accordingly.

    :return: None
    """

    global model
    global scaler
    global data_dict
    global version_model

    try:
        model_name = "stroke_prediction_model_prod"
        alias = "champion"

        mlflow.set_tracking_uri('http://mlflow:5000')
        client = mlflow.MlflowClient()

        # Check in the model registry if the version of the champion has changed
        new_model_data = client.get_model_version_by_alias(model_name, alias)
        new_version_model = int(new_model_data.version)

        # If the versions are not the same
        if new_version_model != version_model:
            # Load the new model and update version and data dictionary
            model, version_model, data_dict = load_model(model_name, alias)

    except:
        # If an error occurs during the process, pass silently
        pass


class ModelInput(BaseModel):
    """
    Input schema for the stroke prediction model.

    This class defines the input fields required by the heart disease prediction model along with their descriptions
    and validation constraints.
    """

    gender: str = Field(
        description="Gender of the patient",
    )
    age: int = Field(
        description="Age of the patient",
        ge=0,
        le=150,
    )
    hypertension: int = Field(
        description="1 if the patient has hypertension",
        ge=0,
        le=1,
    )
    heart_disease: int = Field(
        description="1 if the patient has a heart disease",
        ge=0,
        le=1,
    )
    ever_married: str = Field(
        description="Has the patient ever been married?",
    )
    work_type: str = Field(
        description="Work type of the patient",
    )
    Residence_type: str = Field(
        description="Residence type of the patient",
    )
    avg_glucose_level: float = Field(
        description="Average glucose level in bood of the patient",
        ge=50,
        le=275,
    )
    bmi: float = Field(
        description="Body mass index of the patient",
        ge=0,
        le=100,
    )
    smoking_status: str = Field(
        description="Does the patient smoke?",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "age": 67,
                    "gender": "Female",
                    "hypertension": 1,
                    "heart_disease": 0,
                    "ever_married": "Yes",
                    "work_type": "Self-employed",
                    "Residence_type": "Urban",
                    "avg_glucose_level": 101.45,
                    "bmi": 22.9,
                    "smoking_status": "never smoked",
                }
            ]
        }
    }


class ModelOutput(BaseModel):
    """
    Output schema for the heart disease prediction model.

    This class defines the output fields returned by the heart disease prediction model along with their descriptions
    and possible values.

    :param int_output: Output of the model. True if the patient has a heart disease.
    :param str_output: Output of the model in string form. Can be "Not likely to have a stroke" or "Likely to have a stroke".
    """

    int_output: bool = Field(
        description="Output of the model. True if the patient is likely to get a stroke",
    )
    str_output: Literal["Not likely to have a stroke", "Likely to have a stroke"] = Field(
        description="Output of the model in string form",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "int_output": True,
                    "str_output": "Likely to have a stroke",
                }
            ]
        }
    }


# Load the model before start
model, version_model, data_dict = load_model("stroke_prediction_model_prod", "champion")

app = FastAPI()


@app.get("/")
async def read_root():
    """
    Root endpoint of the Heart Disease Detector API.

    This endpoint returns a JSON response with a welcome message to indicate that the API is running.
    """
    return JSONResponse(content=jsonable_encoder({"message": "Welcome to the Stroke Predictor API"}))


@app.post("/predict/", response_model=ModelOutput)
def predict(
    features: Annotated[
        ModelInput,
        Body(embed=True),
    ],
    background_tasks: BackgroundTasks
):
    """
    Endpoint for stroke prediction.

    This endpoint receives features related to a patient's health and predicts whether the patient has heart disease
    or not using a trained model. It returns the prediction result in both integer and string formats.
    """

    # Extract features from the request and convert them into a list and dictionary
    features_list = [*features.dict().values()]
    features_key = [*features.dict().keys()]

    # Convert features into a pandas DataFrame
    features_df = pd.DataFrame(np.array(features_list).reshape([1, -1]), columns=features_key)
    print(features_df)

    # Process categorical features
    to_drop_map = {
        "gender": "Other",
        "ever_married": "No",
        "work_type": "children",
        "Residence_type": "Rural",
        "smoking_status": "Unknown",
    }
    non_categorical_columns = ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"]
    features_df = apply_one_hot_encoding(features_df, data_dict["categorical_columns"], to_drop_map, non_categorical_columns).astype(float)

    # Reorder DataFrame columns
    features_df = features_df[data_dict["columns_after_dummy"]]

    print("Input:")
    print(features_df.columns)
    print(features_df.values)

    # Scale the data using standard scaler (to review)
    # Load the scaler from MLflow

    # Use scaler logged in mlflow (we need to generalize the run ID)
    # logged_model_uri = 'runs:/d499231d0f3d45619120667a8c242dca/models/scaler'
    # loaded_scaler = mlflow.sklearn.load_model(logged_model_uri)
    # features_df = loaded_scaler.transform(features_df)
    features_df = (features_df - data_dict["standard_scaler_mean"]) / data_dict["standard_scaler_std"]

    # Make the prediction using the trained model
    prediction = model.predict(features_df)

    # Convert prediction result into string format
    str_pred = "Not likely to have a stroke"
    if prediction[0] > 0.5:
        str_pred = "Likely to have a stroke"

    # Check if the model has changed asynchronously
    background_tasks.add_task(check_model)

    print("Output:")
    print(prediction)

    # Return the prediction result
    return ModelOutput(int_output=bool(prediction[0].item()), str_output=str_pred)
