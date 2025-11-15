# Cognitude AI (MVP)

Cognitude AI is a comprehensive LLM proxy and ML model monitoring platform. This backend service, built with FastAPI, provides intelligent caching, multi-provider routing, smart model selection, and complete cost analytics.

## ✨ Core Features

### LLM Proxy Features

- **🔄 OpenAI Compatible**: Drop-in replacement for OpenAI SDK
- **💾 Intelligent Caching**: 30-70% cost savings through Redis-powered response caching
- **🧠 Smart Routing**: Automatic model selection based on task complexity (30-50% additional savings)
- **🌐 Multi-Provider Support**: OpenAI, Anthropic, Hugging Face, Groq
- **💰 Cost Tracking**: Accurate per-request cost calculation and analytics
- **📊 Advanced Analytics**: Usage metrics, recommendations, and insights
- **⚡ High Performance**: Sub-10ms cache lookups, 5x faster than traditional caching

### ML Monitoring Features

- **Organization Auth**: Secure multi-tenant API key management
- **Model Registry**: Register and track ML models
- **Prediction Logging**: Real-time prediction data capture
- **Drift Detection**: Automated data drift analysis

🛠️ Tech Stack
Backend: FastAPI (Python)

Database: PostgreSQL (managed via Docker)

Testing: Pytest and HTTPX

🚀 How to Run This Project
Follow these steps to get the application running locally.

1. Prerequisites
   Python 3.10+

Docker Desktop (must be running)

2. Initial Setup
   Clone the repository:

Bash

git clone https://github.com/your-username/cognitude_mvp.git
cd cognitude_mvp
Create and activate a virtual environment:

Bash

python3 -m venv venv
source venv/bin/activate
Create your .env file: This file holds all your secrets.

Bash

# Generate a random SECRET_KEY for JWT

echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
Now, manually open the .env file and add your Gemini API key and database URL. The file should look like this:

.env

Ini, TOML

SECRET_KEY="your-generated-key-here"
GEMINI_API_KEY="your-google-api-key-here"
DATABASE_URL="postgresql+psycopg2://myuser:mypassword@localhost/mydatabase"
Install Python dependencies:

Bash

pip install -r requirements.txt 3. Run the Application
Start the Database: Open a terminal and run this command to start the PostgreSQL database in a Docker container.

Bash

docker-compose up -d
Start the FastAPI Server: In the same terminal, run the uvicorn server. The --reload flag will automatically restart the server when you make code changes.

Bash

uvicorn app.main:app --reload
You're done! The API is now running on http://127.0.0.1:8000.

🧪 How to Test the API
The easiest way to test is using the built-in documentation.

Open the API Docs: Go to http://127.0.0.1:8000/docs in your browser.

Step 1: Register an Organization

Find POST /auth/register and click "Try it out".

In the request body, enter:

JSON

{ "name": "My Test Company" }
Click "Execute".

Copy the api_key from the 200 OK response.

Step 2: Authenticate

At the top of the page, click the "Authorize" button.

In the "Value" box, type Bearer (with a space) and paste your api_key.

Click "Authorize" and "Close". You are now authenticated.

Step 3: Register a Model

Find POST /models and click "Try it out".

In the request body, enter:

JSON

{
"name": "Production Fraud Model",
"version": "1.0.0",
"description": "My first model",
"features": [
{ "feature_name": "amount", "feature_type": "continuous", "order": 1 }
]
}
Click "Execute".

You will get a 200 OK response. Note the id of your new model (e.g., id: 1).

Step 4: Log a Prediction

Find POST /api/v1/models/{model_id}/predictions and click "Try it out".

Enter the model_id from the previous step (e.g., 1).

In the request body, enter:

JSON

{
"predictions": [
{
"features": { "amount": 120.50 },
"prediction_value": 0.05,
"timestamp": "2025-11-02T10:00:00Z"
}
]
}
Click "Execute". You will get a 200 OK response.

Running Automated Tests
You can also run the complete test suite.

Bash

# Make sure your (venv) is active

pytest
