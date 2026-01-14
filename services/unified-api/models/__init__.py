"""PyDAL model definitions for WaddlePerf Unified API"""

from .user import define_user_models
from .organization import define_organization_models
from .device import define_device_models
from .test import define_test_models
from .token import define_token_models


def define_all_models(db):
    """Define all PyDAL tables for WaddlePerf.

    Args:
        db: PyDAL DAL instance
    """
    define_user_models(db)
    define_organization_models(db)
    define_device_models(db)
    define_test_models(db)
    define_token_models(db)


__all__ = [
    'define_all_models',
    'define_user_models',
    'define_organization_models',
    'define_device_models',
    'define_test_models',
    'define_token_models',
]
