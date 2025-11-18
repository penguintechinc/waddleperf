"""Database models for managerServer"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import secrets

db = SQLAlchemy()

class OrganizationUnit(db.Model):
    __tablename__ = 'organization_units'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('User', backref='organization', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    role = db.Column(db.Enum('global_admin', 'global_reporter', 'ou_admin', 'ou_reporter', 'user'),
                     nullable=False, default='user')
    ou_id = db.Column(db.Integer, db.ForeignKey('organization_units.id'), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        """Hash and set password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure 64-character API key"""
        return secrets.token_hex(32)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'ou_id': self.ou_id,
            'mfa_enabled': self.mfa_enabled,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            data['api_key'] = self.api_key
            data['mfa_secret'] = self.mfa_secret
        return data

class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data = db.Column(db.JSON)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='sessions')

class JWTToken(db.Model):
    __tablename__ = 'jwt_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='jwt_tokens')

class SystemConfig(db.Model):
    """System configuration table (FleetDM-style global settings)"""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text)
    config_type = db.Column(db.Enum('string', 'boolean', 'integer', 'json'), default='string', nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'config_key': self.config_key,
            'config_value': self.config_value,
            'config_type': self.config_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class OUEnrollmentSecret(db.Model):
    """OU enrollment secrets (FleetDM-style team secrets)"""
    __tablename__ = 'ou_enrollment_secrets'

    id = db.Column(db.Integer, primary_key=True)
    ou_id = db.Column(db.Integer, db.ForeignKey('organization_units.id'), nullable=False)
    secret = db.Column(db.String(128), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('OrganizationUnit', backref='enrollment_secrets')

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure enrollment secret (similar to FleetDM)"""
        return secrets.token_urlsafe(48)  # ~64 characters base64url encoded

    def to_dict(self, include_secret=False):
        data = {
            'id': self.id,
            'ou_id': self.ou_id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_secret:
            data['secret'] = self.secret
        return data

class DeviceEnrollment(db.Model):
    """Device enrollments (FleetDM-style host tracking)"""
    __tablename__ = 'device_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    ou_id = db.Column(db.Integer, db.ForeignKey('organization_units.id'), nullable=False)
    enrollment_secret_id = db.Column(db.Integer, db.ForeignKey('ou_enrollment_secrets.id'), nullable=False)
    device_serial = db.Column(db.String(255), unique=True, nullable=False, index=True)
    device_hostname = db.Column(db.String(255), nullable=False)
    device_os = db.Column(db.String(100), nullable=False)
    device_os_version = db.Column(db.String(100), nullable=False)
    client_type = db.Column(db.Enum('containerClient', 'goClient', 'webClient'), nullable=False)
    client_version = db.Column(db.String(50))
    enrolled_ip = db.Column(db.String(45), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, index=True)

    organization = db.relationship('OrganizationUnit', backref='devices')
    enrollment_secret = db.relationship('OUEnrollmentSecret', backref='devices')

    def to_dict(self):
        return {
            'id': self.id,
            'ou_id': self.ou_id,
            'device_serial': self.device_serial,
            'device_hostname': self.device_hostname,
            'device_os': self.device_os,
            'device_os_version': self.device_os_version,
            'client_type': self.client_type,
            'client_version': self.client_version,
            'enrolled_ip': self.enrolled_ip,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active,
        }

class ClientConfig(db.Model):
    """Client test configuration per OU"""
    __tablename__ = 'client_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ou_id = db.Column(db.Integer, db.ForeignKey('organization_units.id'), nullable=True)
    config_name = db.Column(db.String(255), nullable=False)
    config_data = db.Column(db.JSON, nullable=False)
    is_default = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ou_id': self.ou_id,
            'config_name': self.config_name,
            'config_data': self.config_data,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
