# Using a lightweight Python base image
FROM python:3.11-slim

# Setting the working directory inside the container
WORKDIR /app

# Installing the OpenMP runtime required by XGBoost / scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Installing the Python dependencies first (cached layer when only app code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copying the application code and the serialized model
COPY . .

# Port on which the API is served
EXPOSE 7860

# Serving the Flask app (object 'superkart_api' in app.py) with gunicorn
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:7860", "app:superkart_api"]
