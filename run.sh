#!/bin/bash

# Start OceanBase container
echo "Starting OceanBase container..."
docker-compose up -d

# Wait for OceanBase to start
echo "Waiting for OceanBase to start (this may take a minute)..."
sleep 30

# Create database
echo "Creating database..."
docker exec -it oceanbase obclient -h127.0.0.1 -P2881 -uroot -poceanbase -A -e "CREATE DATABASE IF NOT EXISTS test;"

# Activate Python virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the application
echo "Starting the application..."
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
