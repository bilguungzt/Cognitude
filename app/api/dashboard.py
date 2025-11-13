from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy import func, case
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])