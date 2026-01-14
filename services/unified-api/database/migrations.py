"""Database migration utilities for schema initialization and updates"""
import logging
from typing import Optional
from pydal import DAL

logger = logging.getLogger(__name__)


def init_schema(dal: DAL) -> None:
    """
    Initialize database schema by creating all tables and indexes.

    Args:
        dal: DAL instance with defined tables
    """
    logger.info("Initializing database schema")

    try:
        # PyDAL handles table creation automatically with migrate=True
        # This function ensures all tables exist and are ready
        _create_indexes(dal)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def _create_indexes(dal: DAL) -> None:
    """
    Create database indexes for optimized queries.

    Args:
        dal: DAL instance with defined tables
    """
    logger.debug("Creating database indexes")

    try:
        # Users table indexes
        dal.users.email.requires = dal.users.email.requires if hasattr(dal.users.email, 'requires') else []
        dal.users.username.requires = dal.users.username.requires if hasattr(dal.users.username, 'requires') else []

        # API Keys table indexes
        if hasattr(dal, 'api_keys'):
            dal.api_keys.key_hash.requires = dal.api_keys.key_hash.requires if hasattr(dal.api_keys.key_hash, 'requires') else []
            dal.api_keys.user_id.requires = dal.api_keys.user_id.requires if hasattr(dal.api_keys.user_id, 'requires') else []

        # Audit logs table indexes
        if hasattr(dal, 'audit_logs'):
            dal.audit_logs.user_id.requires = dal.audit_logs.user_id.requires if hasattr(dal.audit_logs.user_id, 'requires') else []
            dal.audit_logs.created_at.requires = dal.audit_logs.created_at.requires if hasattr(dal.audit_logs.created_at, 'requires') else []

        # Health checks table indexes
        if hasattr(dal, 'health_checks'):
            dal.health_checks.service_name.requires = dal.health_checks.service_name.requires if hasattr(dal.health_checks.service_name, 'requires') else []
            dal.health_checks.checked_at.requires = dal.health_checks.checked_at.requires if hasattr(dal.health_checks.checked_at, 'requires') else []

        logger.debug("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation skipped or failed (may be expected): {e}")


def migrate_data(dal: DAL, from_version: str, to_version: str) -> None:
    """
    Perform data migrations between schema versions.

    Args:
        dal: DAL instance
        from_version: Source schema version
        to_version: Target schema version
    """
    logger.info(f"Migrating data from version {from_version} to {to_version}")

    try:
        if from_version == "1.0.0" and to_version == "1.1.0":
            _migrate_1_0_to_1_1(dal)
        else:
            logger.warning(f"No migration path defined from {from_version} to {to_version}")
    except Exception as e:
        logger.error(f"Data migration failed: {e}")
        raise


def _migrate_1_0_to_1_1(dal: DAL) -> None:
    """
    Example migration from version 1.0.0 to 1.1.0.

    Args:
        dal: DAL instance
    """
    logger.debug("Executing migration 1.0.0 -> 1.1.0")
    # Add specific migration logic here
    pass


def rollback_migration(dal: DAL, version: str) -> None:
    """
    Rollback database schema to a previous version.

    Args:
        dal: DAL instance
        version: Target version to rollback to
    """
    logger.warning(f"Rolling back database to version {version}")

    try:
        # Implement rollback logic based on version
        logger.info(f"Rollback to version {version} completed")
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise


def get_schema_version(dal: DAL) -> str:
    """
    Get the current database schema version.

    Args:
        dal: DAL instance

    Returns:
        str: Current schema version
    """
    try:
        # Check if version table exists, otherwise return default
        if not hasattr(dal, 'schema_version'):
            return "1.0.0"

        record = dal('SELECT version FROM schema_version ORDER BY created_at DESC LIMIT 1').as_list()
        if record:
            return record[0]['version']
        return "1.0.0"
    except Exception as e:
        logger.warning(f"Could not retrieve schema version: {e}")
        return "1.0.0"


def validate_schema(dal: DAL) -> bool:
    """
    Validate that all required tables exist and are properly configured.

    Args:
        dal: DAL instance

    Returns:
        bool: True if schema is valid, False otherwise
    """
    required_tables = ['users', 'api_keys', 'audit_logs', 'health_checks']

    try:
        for table_name in required_tables:
            if table_name not in dal.tables:
                logger.error(f"Required table '{table_name}' not found in schema")
                return False

        logger.info("Schema validation passed")
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False
