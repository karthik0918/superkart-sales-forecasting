# ---------------------------------------------------------------
# SuperKart Sales Forecasting - Flask backend API
# ---------------------------------------------------------------
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

# Initialising the Flask application
superkart_api = Flask("SuperKart Sales Forecasting API")

# Keeping the order of keys in JSON responses (so batch predictions stay in row order)
superkart_api.json.sort_keys = False

# Loading the serialized pipeline (preprocessing + model) once, when the server starts
model = joblib.load("backend_files/superkart_model.joblib")

# Reference year used during training to compute Store_Age_Years
CURRENT_YEAR = 2026

# Product types grouped as perishables during training
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]

# Features expected by the model, in training order
FEATURES = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def prepare_features(df):
    """
    Returns a model-ready DataFrame with the expected feature columns.
    If raw columns (Product_Id, Store_Establishment_Year, Product_Type) are supplied instead of the
    engineered ones, the engineered features are derived exactly as during training.
    """
    df = df.copy()

    # Same data cleaning as training
    if "Product_Sugar_Content" in df.columns:
        df["Product_Sugar_Content"] = df["Product_Sugar_Content"].replace("reg", "Regular")

    # Same feature engineering as training (only when the engineered column is not already provided)
    if "Product_Id_char" not in df.columns and "Product_Id" in df.columns:
        df["Product_Id_char"] = df["Product_Id"].astype(str).str[:2]
    if "Store_Age_Years" not in df.columns and "Store_Establishment_Year" in df.columns:
        df["Store_Age_Years"] = CURRENT_YEAR - pd.to_numeric(df["Store_Establishment_Year"])
    if "Product_Type_Category" not in df.columns and "Product_Type" in df.columns:
        df["Product_Type_Category"] = np.where(
            df["Product_Type"].isin(PERISHABLES), "Perishables", "Non Perishables"
        )

    # Validating that every required feature is present
    missing = [col for col in FEATURES if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature(s): {missing}")

    # Making sure numeric fields are numeric (raises ValueError on invalid values)
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].apply(pd.to_numeric)

    return df[FEATURES]


# Home route - simple welcome message
@superkart_api.get("/")
def home():
    return "Welcome to the SuperKart Sales Forecasting API!"


# Health-check route - useful to confirm the container is up
@superkart_api.get("/health")
def health():
    return jsonify({"status": "ok"})


# Online (single record) prediction endpoint
@superkart_api.post("/v1/predict")
def predict_sales():
    # Reading the JSON payload from the request
    product_data = request.get_json(silent=True)
    if not isinstance(product_data, dict) or not product_data:
        return jsonify({"error": "Request body must be a non-empty JSON object."}), 400

    # Converting the payload into a model-ready DataFrame
    try:
        input_df = prepare_features(pd.DataFrame([product_data]))
    except (ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400

    # Predicting the product-store sales revenue
    prediction = float(model.predict(input_df)[0])

    # Returning the prediction as JSON
    return jsonify({"Predicted Sales": round(prediction, 2)})


# Batch prediction endpoint - accepts a CSV file uploaded under the key 'file'
@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    if "file" not in request.files:
        return jsonify({"error": "Please upload a CSV file under the key 'file'."}), 400

    # Reading the uploaded CSV into a DataFrame
    try:
        batch_df = pd.read_csv(request.files["file"])
    except Exception as err:
        return jsonify({"error": f"Could not read the CSV file: {err}"}), 400

    if batch_df.empty:
        return jsonify({"error": "The uploaded CSV file has no rows."}), 400

    # Converting the batch into a model-ready DataFrame
    try:
        input_df = prepare_features(batch_df)
    except (ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400

    # Predicting for all rows at once
    predictions = model.predict(input_df)

    # Returning a dictionary of {row index: predicted sales}
    result = {str(idx): round(float(pred), 2) for idx, pred in zip(batch_df.index, predictions)}
    return jsonify(result)


# Running the app directly (inside Docker the app is served by gunicorn instead)
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
