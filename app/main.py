from fastapi import FastAPI
from sqlalchemy import text

from . import database, models
from .api import auth, drift, predictions
from .api import models as api_models

app = FastAPI(title="DriftGuard AI")

@app.on_event("startup")
async def on_startup():
    models.Base.metadata.create_all(bind=database.engine)
    with database.engine.connect() as conn:
        conn.execute(text("SELECT create_hypertable('predictions', 'time', if_not_exists => TRUE);"))
        conn.commit()

app.include_router(auth.router)
app.include_router(api_models.router)
app.include_router(predictions.router)
app.include_router(drift.router)

@app.get("/")
async def root():
    return {"message": "DriftGuard AI is running"}