#!/bin/bash

# Create directory structure
mkdir -p app/api/v1/endpoints
mkdir -p app/core
mkdir -p app/db
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/scheduler
mkdir -p data

# Create empty files
touch app/api/v1/endpoints/forecast.py
touch app/api/v1/endpoints/earthquakes.py
touch app/api/v1/router.py
touch app/core/config.py
touch app/core/database.py
touch app/db/models.py
touch app/schemas/earthquake.py
touch app/services/ingester.py
touch app/services/ml_engine.py
touch app/scheduler/cron.py
touch app/main.py
touch requirements.txt
touch .env
touch data/model.json

echo "Directory structure created successfully!"
