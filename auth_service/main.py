from fastapi import FastAPI
from .routers import auth_router

auth_app = FastAPI(title="Auth Service", version="0.1.0")
auth_app.include_router(auth_router.router, prefix="/auth", tags=["auth"])