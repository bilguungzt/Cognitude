import os
from dotenv import load_dotenv
from agents.router import SmartAIRouter
from agents.project_manager_agent import ProjectManagerAgent

# Load .env file (GEMINI_API_KEY) from the root
load_dotenv()

# ---
# YOUR MVP PROMPT
# This is based on your "DriftGuard-MVP-Spec.md"
# ---
YOUR_BIG_IDEA = """
Build the backend for my 'DriftGuard AI' MVP.
The tech stack is FastAPI, PostgreSQL with TimescaleDB, and React.

The file structure MUST be:
- 'app/main.py': The main FastAPI app.
- 'app/database.py': SQLAlchemy + TimescaleDB setup.
- 'app/models.py': All 6 SQLAlchemy tables from my spec.
- 'app/schemas.py': All Pydantic schemas for API I/O.
- 'app/crud.py': All database functions.
- 'app/security.py': All auth functions (API key verification).
- 'app/api/auth.py': A router with 'POST /auth/register'
- 'app/api/models.py': A router with 'GET /models' and 'POST /models'.
- 'app/api/predictions.py': A router with 'POST /models/{model_id}/predictions'.
- 'app/api/drift.py': A router with 'GET /models/{model_id}/drift/current'.

The database schema MUST include:
1. 'organizations': (name, api_key)
2. 'models': (organization_id, name, model_type, baseline_mean, baseline_std)
3. 'model_features': (model_id, feature_name, feature_type, baseline_stats JSONB)
4. 'predictions': (time TIMESTAMPTZ, model_id, prediction_value, features JSONB)
5. 'drift_alerts': (model_id, alert_type, drift_score)
6. 'alert_channels': (organization_id, channel_type, configuration JSONB)
"""
# ---
# End of prompt
# ---

def main():
    # 1. Initialize the "phone system"
    #    (Make sure your Ollama app is running!)
    router = SmartAIRouter()
    
    # 2. Initialize the "AI Project Manager"
    pm = ProjectManagerAgent(router)
    
    # 3. Give the PM the "Big Idea" and tell it to start
    pm.build_complete_app(idea=YOUR_BIG_IDEA)

if __name__ == "__main__":
    main()
