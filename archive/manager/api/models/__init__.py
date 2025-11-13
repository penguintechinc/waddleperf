from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .test_result import TestResult

__all__ = ['db', 'User', 'TestResult']
