"""SQLAlchemy database schema definitions for initialization"""
import logging
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String,
    Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.sql import func
from datetime import datetime

logger = logging.getLogger(__name__)


def get_sqlalchemy_engine(config):
    """
    Create SQLAlchemy engine for schema initialization.

    Args:
        config: Configuration object with database settings

    Returns:
        SQLAlchemy Engine instance
    """
    db_uri = config.get_db_uri()
    # Convert PyDAL URI format to SQLAlchemy format
    if db_uri.startswith('mysql://'):
        db_uri = db_uri.replace('mysql://', 'mysql+pymysql://')
    elif db_uri.startswith('postgres://'):
        db_uri = db_uri.replace('postgres://', 'postgresql+psycopg2://')

    engine = create_engine(db_uri, echo=False, pool_pre_ping=True)
    return engine


def initialize_schema(config):
    """
    Initialize database schema using SQLAlchemy.
    This should be called once at application startup to create tables.

    Args:
        config: Configuration object with database settings
    """
    engine = get_sqlalchemy_engine(config)
    metadata = MetaData()

    # Users table (for authentication)
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('email', String(255), unique=True, nullable=False),
        Column('username', String(100), unique=True, nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('first_name', String(100)),
        Column('last_name', String(100)),
        Column('is_active', Boolean, default=True),
        Column('role', String(50), default='viewer'),  # admin, maintainer, viewer
        Column('mfa_enabled', Boolean, default=False),
        Column('mfa_secret', String(255)),
        Column('last_login', DateTime(timezone=True)),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    # Refresh tokens table
    refresh_tokens = Table('refresh_tokens', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('token', String(500), unique=True, nullable=False),
        Column('expires_at', DateTime(timezone=True), nullable=False),
        Column('is_revoked', Boolean, default=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
    )

    # Password reset tokens table
    password_reset_tokens = Table('password_reset_tokens', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('token', String(500), unique=True, nullable=False),
        Column('expires_at', DateTime(timezone=True), nullable=False),
        Column('is_used', Boolean, default=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
    )

    # API Keys table for service-to-service auth
    api_keys = Table('api_keys', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('key_hash', String(255), unique=True, nullable=False),
        Column('name', String(100)),
        Column('is_active', Boolean, default=True),
        Column('last_used', DateTime(timezone=True)),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
    )

    # Audit log table
    audit_logs = Table('audit_logs', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='SET NULL')),
        Column('action_type', String(100), nullable=False),  # Renamed from 'action' to avoid reserved keyword
        Column('resource_type', String(100)),
        Column('resource_id', String(100)),
        Column('details', Text),
        Column('ip_address', String(45)),  # IPv6 support
        Column('user_agent', String(255)),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
    )

    # Health checks data table
    health_checks = Table('health_checks', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('service_name', String(100), nullable=False),
        Column('status', String(20), nullable=False),  # healthy, degraded, unhealthy
        Column('status_message', Text),  # Renamed from 'message' to avoid reserved keyword
        Column('response_time_ms', Integer),
        Column('checked_at', DateTime(timezone=True), server_default=func.now()),
    )

    # Create indexes for performance
    Index('idx_users_email', users.c.email)
    Index('idx_api_keys_hash', api_keys.c.key_hash)
    Index('idx_audit_logs_user_id', audit_logs.c.user_id)
    Index('idx_audit_logs_created_at', audit_logs.c.created_at)
    Index('idx_health_checks_service', health_checks.c.service_name)
    Index('idx_health_checks_checked_at', health_checks.c.checked_at)

    # Create all tables
    logger.info("Creating database schema with SQLAlchemy...")
    metadata.create_all(engine, checkfirst=True)
    logger.info("Database schema created successfully")

    engine.dispose()
