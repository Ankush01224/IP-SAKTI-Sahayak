import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.db.session import init_db, SessionLocal
from app.ingestion.ingest_pipeline import IngestPipeline
from app.utils.logger import logger

def main():
    logger.info("Initializing database...")
    init_db()
    db = SessionLocal()
    try:
        pipeline = IngestPipeline(db)
        logger.info(f"Ingesting regulatory seed corpus from: {settings.SEED_CORPUS_DIR}")
        results = pipeline.ingest_directory(settings.SEED_CORPUS_DIR)
        logger.info(f"Successfully processed {len(results)} seed documents.")
        for r in results:
            if "document" in r:
                logger.info(f" - [{r['document'].jurisdiction}] {r['document'].title}: {r['chunks_created']} chunks")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
