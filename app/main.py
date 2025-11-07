from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, models, predictions, drift, alert_channels
from .database import Base, engine, apply_migrations
from .services.background_tasks import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    apply_migrations()
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="DriftAssure AI",
    description="""
## ML Model Monitoring & Drift Detection Platform

DriftAssure AI helps ML teams detect data drift in production models and get alerted before model performance degrades.

### Features

* **Model Registration**: Register your ML models with feature definitions
* **Prediction Logging**: Log predictions in real-time or batch
* **Drift Detection**: Automatic KS test-based drift detection every 15 minutes
* **Alerts**: Email and Slack notifications when drift is detected
* **API Keys**: Secure multi-tenant authentication

### Quick Start

1. Register your organization: `POST /auth/register`
2. Create a model: `POST /models/`
3. Log predictions: `POST /predictions/models/{model_id}/predictions`
4. Configure alerts: `POST /alert-channels/`
5. Check drift: `GET /drift/models/{model_id}/drift/current`

### Authentication

All endpoints (except `/auth/register`) require an API key in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key" https://api.driftassure.com/models/
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "DriftAssure Support",
        "url": "https://driftassure.com/support",
        "email": "support@driftassure.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Production frontend
        "http://localhost:8080",  # Alternative frontend port
        "https://driftassure-frontend-c83ok9o36-bilguungzts-projects.vercel.app",  # Vercel deployment
        "https://*.vercel.app",  # All Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(drift.router, prefix="/drift", tags=["drift"])
app.include_router(alert_channels.router, prefix="/alert-channels", tags=["alert-channels"])

@app.get("/")
def read_root():
    return {"message": "DriftAssure AI is running"}

@app.get("/health", tags=["system"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    return {
        "status": "healthy",
        "service": "DriftAssure AI",
        "version": "1.0.0",
        "timestamp": "2025-11-06T00:00:00Z"
    }

@app.get("/scheduler/status", tags=["system"])
def scheduler_status():
    """
    Get status of background scheduler
    """
    jobs = scheduler.get_jobs()
    
    return {
        "is_running": scheduler.running,
        "job_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }
