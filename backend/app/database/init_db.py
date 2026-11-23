from backend.app.database.session import engine, Base
from backend.app.models import VehicleDetection, LicensePlate, Violation, ProcessingJob
from backend.app.core.logger import logger


def init_db():
    """Initializes SQLite database tables and applies WAL mode for high concurrency."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # Enable WAL mode for SQLite
    with engine.connect() as connection:
        try:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
            connection.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            logger.info("SQLite WAL (Write-Ahead-Logging) and NORMAL sync successfully configured.")
        except Exception as e:
            logger.warning(f"Could not set SQLite pragmas: {e}")

    logger.info("Database schema created successfully.")


if __name__ == "__main__":
    init_db()
