from contextlib import asynccontextmanager

from fastapi import FastAPI

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


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(drift.router, prefix="/drift", tags=["drift"])
app.include_router(alert_channels.router, prefix="/alert-channels", tags=["alert-channels"])

@app.get("/")
def read_root():
    return {"message": "DriftGuard AI is running"}
