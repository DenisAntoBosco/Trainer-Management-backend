from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .controllers.auth_controller import router as auth_router
from .controllers.user_controller import router as user_router
from .controllers.trainer_controller import router as trainer_router
from .controllers.project_controller import router as project_router
from .controllers.batch_controller import router as batch_router
from .controllers.hr_request_controller import router as hr_router
from .controllers.attendance_controller import router as attendance_router
from .core.rate_limiter import limiter
from .middleware.error_handler import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from .core.logging_config import logger

app = FastAPI(
    title="Training Management System API",
    description="Complete REST API for Training Management System",
    version="1.0.0"
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/v1")
app.include_router(user_router, prefix="/v1")
app.include_router(trainer_router, prefix="/v1")
app.include_router(project_router, prefix="/v1")
app.include_router(batch_router, prefix="/v1")
app.include_router(hr_router, prefix="/v1")
app.include_router(attendance_router, prefix="/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

@app.get("/")
async def root():
    return {"message": "Training Management System API", "version": "1.0.0"}

@app.get("/api/document/healthCheck")
async def health_check():
    return {"status": "healthy"}