from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import time

from app.config import get_settings
from app.database import init_db, engine
from app.routers import auth, transactions, coaching, stokvel, ussd, voice, cards, payments, wallet

settings = get_settings()

# Structured logging
logging.basicConfig(
    level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")
    # Never let a database problem take the whole service down: if init_db()
    # raises here, the workers die on boot and Render answers every request
    # (including /health) with 502. Log it and start degraded instead.
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed - starting in degraded mode")
    yield
    try:
        await engine.dispose()
    except Exception:
        logger.exception("Error disposing database engine")
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="AI Financial Coach for MoMo users — Scam Shield, Stokvel Intelligence, Multi-Channel Access. Powered by Google Gemini AI.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    if duration > 2.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")
    return response


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(coaching.router, prefix="/api/coaching", tags=["AI Coaching"])
app.include_router(stokvel.router, prefix="/api/stokvels", tags=["Stokvel"])
app.include_router(ussd.router, prefix="/api/ussd", tags=["USSD"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(cards.router)
app.include_router(cards.apple_pay_router)
app.include_router(payments.router)
app.include_router(wallet.router)


@app.get("/")
async def root():
    return {
        "message": "MoMo SmartMoney AI API",
        "version": "2.0.0",
        "status": "running",
        "ai_engine": "Google Gemini 2.0 Flash",
        "features": [
            "AI Financial Coaching",
            "Scam Shield Protection",
            "Stokvel Management",
            "USSD Access (*141*8#)",
            "Voice/IVR Support",
        ],
        "docs": "/docs" if settings.app_env != "production" else "disabled in production",
    }


@app.get("/health")
async def health():
    from sqlalchemy import text

    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    status = "healthy" if db_status == "healthy" else "degraded"
    return {
        "status": status,
        "service": "smartmoney-api",
        "version": "2.0.0",
        "database": db_status,
        "ai": "gemini" if settings.gemini_api_key else "fallback",
        "timestamp": datetime.utcnow().isoformat(),
    }
