from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
        app.state.db_ready = True
        logger.info("Database initialized")
    except Exception:
        app.state.db_ready = False
        logger.exception(
            "DB INIT FAILED - schema was NOT created. Every request that reads or "
            "writes a table will return 500 until this is fixed."
        )
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

_allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]


# ---------------------------------------------------------------------------
# Middleware order matters and is counter-intuitive here.
#
# Starlette's `add_middleware` INSERTS AT THE FRONT, so the middleware added
# LAST ends up outermost. An `@app.exception_handler(Exception)` does not help
# on its own either: that runs in ServerErrorMiddleware, which sits outside
# every user middleware, so the response it builds never passes back through
# CORSMiddleware and still reaches the browser with no
# Access-Control-Allow-Origin - the "MissingAllowOriginHeader" symptom.
#
# So the catch-all is registered FIRST (innermost) and CORS LAST (outermost):
# an unhandled exception becomes a real JSONResponse deep inside the stack and
# then travels out through CORSMiddleware, which stamps the headers on it. The
# browser sees the actual 500 instead of a bogus CORS failure.
# ---------------------------------------------------------------------------


@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "path": request.url.path,
                "error_type": type(exc).__name__,
            },
        )


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    if duration > 2.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")
    return response


# Added last so it is the outermost layer and can decorate error responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time"],
)


# Belt and braces: if something escapes even the middleware stack, still answer
# with JSON rather than Starlette's bare text/plain "Internal Server Error".
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )


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
            # A live connection is not enough: if create_all failed at boot the
            # tables are missing and every real endpoint 500s while SELECT 1
            # still succeeds. Probe an actual table.
            await conn.execute(text("SELECT 1 FROM users LIMIT 1"))
    except Exception:
        db_status = "unhealthy"

    schema_ready = getattr(app.state, "db_ready", None)
    status = "healthy" if db_status == "healthy" else "degraded"
    return {
        "status": status,
        "service": "smartmoney-api",
        "version": "2.0.0",
        "database": db_status,
        "schema_ready": schema_ready,
        "ai": "gemini" if settings.gemini_api_key else "fallback",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/schema")
async def health_schema():
    """Report drift between the SQLAlchemy models and the live database.

    `create_all` only creates missing *tables*, never ALTERs an existing one,
    so a column added to a model after the table was first created stays
    missing forever. That makes `SELECT 1 FROM users` succeed while
    `select(User)` dies with a ProgrammingError - a green /health next to
    500s on every real endpoint. This endpoint names the missing columns
    instead of leaving it to log archaeology.
    """
    from sqlalchemy import inspect as sa_inspect

    from app.database import Base

    def _diff(sync_conn):
        inspector = sa_inspect(sync_conn)
        live_tables = set(inspector.get_table_names())
        missing_tables = []
        missing_columns = {}
        for table in Base.metadata.sorted_tables:
            if table.name not in live_tables:
                missing_tables.append(table.name)
                continue
            present = {c["name"] for c in inspector.get_columns(table.name)}
            gaps = [c.name for c in table.columns if c.name not in present]
            if gaps:
                missing_columns[table.name] = gaps
        return missing_tables, missing_columns

    try:
        async with engine.connect() as conn:
            missing_tables, missing_columns = await conn.run_sync(_diff)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__}

    in_sync = not missing_tables and not missing_columns
    return {
        "status": "in_sync" if in_sync else "drifted",
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "hint": (
            None
            if in_sync
            else "Redeploy: init_db() reconciles these with ALTER TABLE ADD COLUMN."
        ),
    }
