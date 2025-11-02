from fastapi import FastAPI

from .api import auth, models, predictions, drift
from .database import Base, engine

app = FastAPI()

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(drift.router, prefix="/drift", tags=["drift"])

@app.get("/")
def read_root():
    return {"message": "DriftGuard AI is running"}