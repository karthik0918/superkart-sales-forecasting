# ---------------------------------------------------------------
# SuperKart Sales Forecasting - Streamlit frontend
# ---------------------------------------------------------------
import os

import pandas as pd
import requests
import streamlit as st

# URL of the Flask backend. Inside the Docker network the backend container is reachable by its name.
BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860").rstrip("/")

# Same constants as used during training
CURRENT_YEAR = 2026
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]
PRODUCT_TYPES = [
    "Fruits and Vegetables", "Snack Foods", "Frozen Foods", "Dairy", "Household", "Baking Goods",
    "Canned", "Health and Hygiene", "Meat", "Soft Drinks", "Breads", "Hard Drinks", "Others",
    "Starchy Foods", "Breakfast", "Seafood",
]

# Page configuration and title
st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="", layout="centered")
st.title("SuperKart Sales Forecasting")
st.write(
    "Forecast the total sales revenue of a product in a store, either for a single "
    "product-store combination or for a batch of records uploaded as a CSV file."
)

tab_online, tab_batch = st.tabs(["Single prediction", "Batch prediction"])

# ---------------- Online (single) prediction ----------------
with tab_online:
    st.subheader("Product details")
    col1, col2 = st.columns(2)
    with col1:
        product_id_char = st.selectbox(
            "Product group (Product_Id prefix)", ["FD", "NC", "DR"],
            help="FD - Food, NC - Non-Consumable, DR - Drinks",
        )
        product_type = st.selectbox("Product type", PRODUCT_TYPES)
        product_sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
    with col2:
        product_weight = st.number_input("Product weight", min_value=0.0, value=12.66, step=0.01)
        product_mrp = st.number_input("Product MRP", min_value=0.0, value=117.08, step=0.01)
        product_area = st.number_input(
            "Allocated display area (ratio)", min_value=0.0, max_value=1.0,
            value=0.027, step=0.001, format="%.3f",
        )

    st.subheader("Store details")
    col3, col4 = st.columns(2)
    with col3:
        store_type = st.selectbox(
            "Store type", ["Supermarket Type2", "Supermarket Type1", "Departmental Store", "Food Mart"]
        )
        store_size = st.selectbox("Store size", ["Medium", "High", "Small"])
    with col4:
        store_city = st.selectbox("City tier", ["Tier 2", "Tier 1", "Tier 3"])
        store_year = st.number_input(
            "Store establishment year", min_value=1950, max_value=CURRENT_YEAR, value=2009, step=1
        )

    # Building the payload in exactly the format expected by the API
    payload = {
        "Product_Weight": product_weight,
        "Product_Sugar_Content": product_sugar,
        "Product_Allocated_Area": product_area,
        "Product_MRP": product_mrp,
        "Store_Size": store_size,
        "Store_Location_City_Type": store_city,
        "Store_Type": store_type,
        "Product_Id_char": product_id_char,
        "Store_Age_Years": int(CURRENT_YEAR - store_year),
        "Product_Type_Category": "Perishables" if product_type in PERISHABLES else "Non Perishables",
    }

    if st.button("Predict sales", type="primary"):
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if response.status_code == 200:
                prediction = response.json()["Predicted Sales"]
                st.success(f"Forecast sales revenue for this product in this store: **{prediction:,.2f}**")
            else:
                st.error(f"API error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as err:
            st.error(f"Could not reach the backend at {BACKEND_URL}: {err}")

# ---------------- Batch prediction ----------------
with tab_batch:
    st.write(
        "Upload a CSV with the columns: `Product_Weight`, `Product_Sugar_Content`, `Product_Allocated_Area`, "
        "`Product_MRP`, `Store_Size`, `Store_Location_City_Type`, `Store_Type`, `Product_Id_char`, "
        "`Store_Age_Years`, `Product_Type_Category`."
    )
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)
        st.write(f"Preview ({len(batch_df)} rows):")
        st.dataframe(batch_df.head())

        if st.button("Predict batch", type="primary"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/v1/predictbatch",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                    timeout=120,
                )
                if response.status_code == 200:
                    predictions = response.json()
                    results = batch_df.copy()
                    results["Predicted_Sales"] = [predictions[str(i)] for i in range(len(results))]
                    st.success("Batch predictions completed.")
                    st.write(predictions)  # Display the predictions
                else:
                    st.error(f"API error ({response.status_code}): {response.text}")
            except requests.exceptions.RequestException as err:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {err}")
