"""PyDAL database connection manager for runtime operations"""
import logging
import os
import tempfile
from typing import Optional
from pydal import DAL, Field

logger = logging.getLogger(__name__)


def get_dal(config) -> DAL:
    """
    Initialize and return a PyDAL instance for runtime database operations.
    Schema initialization should be done separately using SQLAlchemy.

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
    # Use migrate=False since SQLAlchemy handles schema creation
    # Use secure temp directory for metadata
    dal_folder = os.path.join(tempfile.gettempdir(), 'pydal_metadata')
    os.makedirs(dal_folder, mode=0o700, exist_ok=True)  # Secure permissions: owner-only

    dal = DAL(
        db_uri,
        pool_size=config.DB_POOL_SIZE,
        migrate=False,  # SQLAlchemy handles schema, PyDAL only for operations
        fake_migrate=False,
        check_reserved=['all'],
        folder=dal_folder  # Secure temp directory for metadata
    )

    # Define table schemas for PyDAL to use (must match SQLAlchemy schema)
    _define_models(dal)

    logger.info("PyDAL initialized successfully")
    return dal


def _define_models(dal: DAL) -> None:
    """
    Define table schemas in PyDAL to match SQLAlchemy-created tables.
    This allows PyDAL to perform runtime operations on existing tables.

    Args:
        dal: DAL instance to register models with
    """
    # Users table (for authentication)
    dal.define_table(
        'users',
        Field('id', 'id'),
        Field('email', 'string'),
        Field('username', 'string'),
        Field('password_hash', 'string'),
        Field('first_name', 'string'),
        Field('last_name', 'string'),
        Field('is_active', 'boolean', default=True),
        Field('role', 'string', default='viewer'),
        Field('mfa_enabled', 'boolean', default=False),
        Field('mfa_secret', 'string'),
        Field('last_login', 'datetime'),
        Field('created_at', 'datetime'),
        Field('updated_at', 'datetime'),
        migrate=False  # Don't migrate, table already exists
    )

    # Refresh tokens table
    dal.define_table(
        'refresh_tokens',
        Field('id', 'id'),
        Field('user_id', 'reference users'),
        Field('token', 'string'),
        Field('expires_at', 'datetime'),
        Field('is_revoked', 'boolean', default=False),
        Field('created_at', 'datetime'),
        migrate=False
    )

    # Password reset tokens table
    dal.define_table(
        'password_reset_tokens',
        Field('id', 'id'),
        Field('user_id', 'reference users'),
        Field('token', 'string'),
        Field('expires_at', 'datetime'),
        Field('is_used', 'boolean', default=False),
        Field('created_at', 'datetime'),
        migrate=False
    )

    # API Keys table
    dal.define_table(
        'api_keys',
        Field('id', 'id'),
        Field('user_id', 'reference users'),
        Field('key_hash', 'string'),
        Field('name', 'string'),
        Field('is_active', 'boolean', default=True),
        Field('last_used', 'datetime'),
        Field('created_at', 'datetime'),
        migrate=False
    )

    # Audit log table
    dal.define_table(
        'audit_logs',
        Field('id', 'id'),
        Field('user_id', 'reference users'),
        Field('action_type', 'string'),  # Renamed from 'action' to avoid reserved keyword
        Field('resource_type', 'string'),
        Field('resource_id', 'string'),
        Field('details', 'text'),
        Field('ip_address', 'string'),
        Field('user_agent', 'string'),
        Field('created_at', 'datetime'),
        migrate=False
    )

    # Health checks data table
    dal.define_table(
        'health_checks',
        Field('id', 'id'),
        Field('service_name', 'string'),
        Field('status', 'string'),
        Field('status_message', 'text'),  # Renamed from 'message' to avoid reserved keyword
        Field('response_time_ms', 'integer'),
        Field('checked_at', 'datetime'),
        migrate=False
    )

    logger.info("PyDAL models defined successfully")


def close_dal(dal: DAL) -> None:
    """
    Close the DAL database connection.

    Args:
        dal: DAL instance to close
    """
    if dal:
        dal.close()
        logger.info("Database connection closed")
