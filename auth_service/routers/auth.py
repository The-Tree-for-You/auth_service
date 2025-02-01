from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import the database session
from ..core.database import get_db
from ..models.auth_model import User
from ..schemas.auth_schemas import UserCreate, UserLogin

router = APIRouter()
