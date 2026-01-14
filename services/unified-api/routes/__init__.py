"""Route blueprints for WaddlePerf Unified API"""
from .auth import auth_bp
from .organizations import organizations_bp
from .devices import devices_bp
from .tests import tests_bp
from .stats import stats_bp


__all__ = ['auth_bp', 'organizations_bp', 'devices_bp', 'tests_bp', 'stats_bp']
