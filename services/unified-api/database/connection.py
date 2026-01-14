"""PyDAL database connection manager with multi-database support"""
import logging
from typing import Optional
from pydal import DAL, Field

logger = logging.getLogger(__name__)


def get_dal(config) -> DAL:
    """
    Initialize and return a PyDAL instance with database connection.

    Args:
        config: Configuration object with DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

    Returns:
        DAL: Configured PyDAL instance

    Raises:
        ValueError: If DB_TYPE is invalid or connection fails
    """
    # Validate DB_TYPE
    valid_types = ['postgres', 'mysql', 'sqlite']
    if config.DB_TYPE not in valid_types:
        raise ValueError(f"Invalid DB_TYPE: {config.DB_TYPE}. Must be one of {valid_types}")

    # Build connection URI based on DB_TYPE
    db_uri = config.get_db_uri()

    logger.info(f"Initializing PyDAL with DB_TYPE: {config.DB_TYPE}")

    # Initialize DAL with connection pooling
    dal = DAL(
        db_uri,
        pool_size=config.DB_POOL_SIZE,
        migrate=True,
        fake_migrate=False,
        check_reserved=['all']
    )

    # Call model definition functions to register all tables
    _define_models(dal)

    return dal


def _define_models(dal: DAL) -> None:
    """
    Define all database models/tables.

    Args:
        dal: DAL instance to register models with
    """
    # Users table (for authentication)
    dal.define_table(
        'users',
        Field('email', 'string', unique=True, required=True),
        Field('username', 'string', unique=True, required=True),
        Field('password_hash', 'string', required=True),
        Field('first_name', 'string'),
        Field('last_name', 'string'),
        Field('is_active', 'boolean', default=True),
        Field('role', 'string', default='viewer'),  # admin, maintainer, viewer
        Field('last_login', 'datetime'),
        Field('created_at', 'datetime', default=lambda: __import__('datetime').datetime.utcnow()),
        Field('updated_at', 'datetime', default=lambda: __import__('datetime').datetime.utcnow(),
              update=lambda: __import__('datetime').datetime.utcnow()),
        migrate=True
    )

    # API Keys table for service-to-service auth
    dal.define_table(
        'api_keys',
        Field('user_id', 'reference users', required=True, ondelete='CASCADE'),
        Field('key_hash', 'string', unique=True, required=True),
        Field('name', 'string'),
        Field('is_active', 'boolean', default=True),
        Field('last_used', 'datetime'),
        Field('created_at', 'datetime', default=lambda: __import__('datetime').datetime.utcnow()),
        migrate=True
    )

    # Audit log table
    dal.define_table(
        'audit_logs',
        Field('user_id', 'reference users'),
        Field('action', 'string', required=True),
        Field('resource_type', 'string'),
        Field('resource_id', 'string'),
        Field('details', 'text'),
        Field('ip_address', 'string'),
        Field('user_agent', 'string'),
        Field('created_at', 'datetime', default=lambda: __import__('datetime').datetime.utcnow()),
        migrate=True
    )

    # Health checks data table
    dal.define_table(
        'health_checks',
        Field('service_name', 'string', required=True),
        Field('status', 'string', required=True),  # healthy, degraded, unhealthy
        Field('message', 'text'),
        Field('response_time_ms', 'integer'),
        Field('checked_at', 'datetime', default=lambda: __import__('datetime').datetime.utcnow()),
        migrate=True
    )

    logger.info("Database models defined successfully")


def close_dal(dal: DAL) -> None:
    """
    Close the DAL database connection.

    Args:
        dal: DAL instance to close
    """
    if dal:
        dal.close()
        logger.info("Database connection closed")
