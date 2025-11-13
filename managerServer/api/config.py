"""Configuration module for managerServer API"""
import os
from datetime import timedelta
from dataclasses import dataclass, field

@dataclass
class Config:
    """Application configuration"""

    # Server
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'dev-jwt-secret-change-in-production')
    MANAGER_KEY: str = os.getenv('MANAGER_KEY', '0' * 64)

    # Database
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '3306')
    DB_USER: str = os.getenv('DB_USER', 'waddleperf')
    DB_PASS: str = os.getenv('DB_PASS', '')
    DB_NAME: str = os.getenv('DB_NAME', 'waddleperf')

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = field(default_factory=lambda: {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    })

    # JWT
    JWT_EXPIRATION_HOURS: int = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    @property
    def JWT_EXPIRATION(self) -> timedelta:
        return timedelta(hours=self.JWT_EXPIRATION_HOURS)

    @property
    def JWT_REFRESH_EXPIRATION(self) -> timedelta:
        return timedelta(days=self.JWT_REFRESH_EXPIRATION_DAYS)

    # MFA
    MFA_REQUIRED: bool = os.getenv('MFA_REQUIRED', 'false').lower() == 'true'
    MFA_ISSUER: str = 'WaddlePerf'

    # CORS
    CORS_ORIGINS: list = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*').split(','))

    # API
    API_TITLE: str = 'WaddlePerf Manager API'
    API_VERSION: str = '1.0.0'

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
