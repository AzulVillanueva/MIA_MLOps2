#!/bin/bash

# Download dataset from Kaggle
kaggle datasets download -d fedesoriano/stroke-prediction-dataset
unzip ./stroke-prediction-dataset.zip
rm ./stroke-prediction-dataset.zip
