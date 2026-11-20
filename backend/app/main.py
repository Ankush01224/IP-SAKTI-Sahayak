from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import init_db, SessionLocal
from app.ingestion.ingest_pipeline import IngestPipeline
from app.api.routes import health_router, documents_router, chat_router
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown routines."""
    logger.info("Initializing IP-SAKTI Sahayak platform...")
    # Initialize DB tables
    init_db()

    # Automatically check and seed curated regulatory corpus on first boot
    db = SessionLocal()
    try:
        from app.models.db_models import Document
        existing_count = db.query(Document).count()
        if existing_count == 0 and settings.SEED_CORPUS_DIR.exists():
            logger.info("Empty corpus detected. Commencing automatic ingestion of seed regulatory documents...")
            pipeline = IngestPipeline(db)
            results = pipeline.ingest_directory(settings.SEED_CORPUS_DIR)
            logger.info(f"Auto-seeded {len(results)} regulatory documents.")
        else:
            logger.info(f"Corpus verified: {existing_count} regulatory documents active.")
    except Exception as e:
        logger.error(f"Error during auto-seeding: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down IP-SAKTI Sahayak backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**SIH26045 · Ministry of Ayush**\n\n"
        "A multilingual, RAG-based AI assistant providing source-grounded Intellectual Property (IP) "
        "and regulatory compliance guidance for Ayurveda across national and international regimes."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

# Top-level direct health endpoint
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "sih_statement": "SIH26045 - Ministry of Ayush",
        "docs": "/docs",
        "status": "online"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)} on {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )
