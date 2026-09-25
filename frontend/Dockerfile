# Using a lightweight Python base image
FROM python:3.11-slim

# Setting the working directory inside the container
WORKDIR /app

# Installing the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copying the Streamlit app
COPY . .

# Default backend address on the shared Docker network (can be overridden with -e BACKEND_URL=...)
ENV BACKEND_URL=http://superkart-backend:7860

# Port on which Streamlit is served
EXPOSE 8501

# Running Streamlit; CORS/XSRF checks are disabled so file uploads work behind the Codespaces port-forwarding proxy
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
