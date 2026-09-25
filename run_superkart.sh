#!/usr/bin/env bash
# Builds and runs the SuperKart backend and frontend as separate containers on a shared Docker network.
# Run from the repository root inside the GitHub Codespace:  bash run_superkart.sh
set -e

NETWORK=superkart-net

# Creating the Docker network (ignored if it already exists)
docker network create "$NETWORK" 2>/dev/null || true

# Removing old containers from a previous run, if any
docker rm -f superkart-backend superkart-frontend 2>/dev/null || true

# Building the images
docker build -t superkart-backend ./backend_files
docker build -t superkart-frontend ./frontend_files

# Running the Flask backend (port 7860) - its container name is its hostname on the network
docker run -d --name superkart-backend --network "$NETWORK" -p 7860:7860 superkart-backend

# Running the Streamlit frontend (port 8501), pointing it to the backend by container name
docker run -d --name superkart-frontend --network "$NETWORK" -p 8501:8501 \
  -e BACKEND_URL=http://superkart-backend:7860 superkart-frontend

docker ps
echo "Backend  -> port 7860 | Frontend -> port 8501 (set port 7860 to Public in the Ports tab for API access)"
