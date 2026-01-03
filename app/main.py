from fastapi import FastAPI, Request
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
import traceback

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
    allow_origins=[
        "https://d1l90pfwzzfkwv.cloudfront.net",  # Your frontend CloudFront
        "http://localhost:5173", 
        "http://localhost:8080", 
        "http://localhost:3000",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"🔍 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    # Log all headers for debugging authentication issues
    if request.url.path in ["/v1/users/me", "/v1/auth/refresh"]:
        logger.info(f"📋 Headers received: {dict(request.headers)}")
        auth_header = request.headers.get("authorization")
        refresh_header = request.headers.get("x-refresh-token")
        logger.info(f"🔐 Authorization header: {auth_header[:50] + '...' if auth_header else 'None'}")
        logger.info(f"🔄 X-Refresh-Token header: {refresh_header[:50] + '...' if refresh_header else 'None'}")
    
    try:
        response = await call_next(request)
        logger.info(f"✅ {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Include routers
try:
    logger.info("🔧 Registering routers...")
    app.include_router(auth_router, prefix="/v1")
    logger.info("✅ Auth router registered")
    app.include_router(user_router, prefix="/v1")
    logger.info("✅ User router registered")
    app.include_router(trainer_router, prefix="/v1")
    logger.info("✅ Trainer router registered")
    app.include_router(project_router, prefix="/v1")
    logger.info("✅ Project router registered")
    app.include_router(batch_router, prefix="/v1")
    logger.info("✅ Batch router registered")
    app.include_router(hr_router, prefix="/v1")
    logger.info("✅ HR router registered")
    app.include_router(attendance_router, prefix="/v1")
    logger.info("✅ Attendance router registered")
    logger.info("✅ All routers registered successfully")
except Exception as e:
    logger.error(f"❌ Error registering routers: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Application starting up...")
    try:
        # Test database connection
        from .core.database import get_db
        from sqlalchemy import text
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            break
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Application shutting down...")

@app.get("/")
async def root():
    logger.info("🏠 Root endpoint called")
    return {"message": "Training Management System API", "version": "1.0.0"}

@app.options("/{path:path}")
async def options_handler(path: str):
    logger.info(f"🔧 OPTIONS request for path: {path}")
    return {"message": "OK"}

@app.get("/test-db")
async def test_database():
    logger.info("📊 Database test endpoint called")
    try:
        from .core.database import get_db
        from sqlalchemy import text
        async for db in get_db():
            result = await db.execute(text("SELECT 1 as test"))
            row = result.first()
            logger.info(f"✅ Database test successful: {row}")
            return {"status": "database connected", "test_result": dict(row._mapping) if row else None}
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "database error", "error": str(e)}

@app.get("/api/document/healthCheck")
async def health_check():
    logger.info("❤️ Health check endpoint called")
    return {"status": "healthy"}