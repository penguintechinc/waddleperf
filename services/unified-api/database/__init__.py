"""Database initialization module for WaddlePerf Unified API"""
from pydal import DAL
from config import Config


def initialize_db(config: Config) -> DAL:
    """Initialize PyDAL database connection.

    Args:
        config: Configuration object

    Returns:
        DAL instance
    """
    db_uri = config.get_db_uri()
    db = DAL(
        db_uri,
        pool_size=config.DB_POOL_SIZE,
        migrate=True,
        fake_migrate=False,
    )
    return db
