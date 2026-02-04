# score.py
import json
import os
import numpy as np
import pandas as pd
import joblib


def init():
    """
    Azure ML calls init() once when the container starts.
    We load the trained sklearn Pipeline (preprocessor + model).
    """
    global model

    # Azure standard: model is placed under AZUREML_MODEL_DIR (if you deploy from "model" asset)
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    model_path = os.path.join(model_dir, "car_price_pipeline.pkl")

    # If you deploy by just including the file in the image, fallback to local path
    if not os.path.exists(model_path):
        model_path = "car_price_pipeline.pkl"

    model = joblib.load(model_path)


def _to_dataframe(payload: dict) -> pd.DataFrame:
    """
    Accept common Azure payload shapes:
      - {"data": [{...}, {...}]}
      - {"input_data": [{...}, {...}]}
      - {"data": {"col1":[...], "col2":[...]}}  (optional)
    """
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    if "data" in payload:
        data = payload["data"]
    elif "input_data" in payload:
        data = payload["input_data"]
    else:
        # allow sending a single record directly
        # e.g. {"Make":"VW", "Year":2015, ...}
        data = payload

    # If they send a single dict record, wrap it
    if isinstance(data, dict):
        # could be record-like or column-oriented; try record first
        # If values are scalars -> one row; if lists -> DataFrame handles it
        try:
            df = pd.DataFrame([data])
        except Exception:
            df = pd.DataFrame(data)
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        raise ValueError("Unsupported input format. Use dict or list of dicts under 'data' / 'input_data'.")

    return df


def run(raw_data):
    """
    Azure ML calls run() per request.
    raw_data is usually a JSON string.
    """
    try:
        if isinstance(raw_data, (bytes, bytearray)):
            raw_data = raw_data.decode("utf-8")

        # Azure usually passes JSON string; but sometimes already dict
        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        df = _to_dataframe(payload)

        # Predict
        preds = model.predict(df)

        # Ensure JSON-serializable
        preds = np.asarray(preds).astype(float).tolist()

        return {
            "predictions": preds,
            "n_rows": len(preds)
        }

    except Exception as e:
        # Return error in a clear JSON shape
        return {
            "error": str(e)
        }
