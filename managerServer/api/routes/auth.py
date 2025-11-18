"""Authentication routes for managerServer API"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
import pyotp
from models import db, User, JWTToken
from config import Config

auth_bp = Blueprint('auth', __name__)
cfg = Config()

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login with username/password, returns JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    mfa_code = data.get('mfa_code')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check MFA if enabled
    if user.mfa_enabled:
        if not mfa_code:
            return jsonify({'error': 'MFA code required', 'mfa_required': True}), 401

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code):
            return jsonify({'error': 'Invalid MFA code'}), 401

    # Generate JWT
    token = generate_jwt(user.id)

    # Store token hash in database
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    jwt_token = JWTToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + cfg.JWT_EXPIRATION
    )
    db.session.add(jwt_token)
    db.session.commit()

    return jsonify({
        'token': token,
        'user': user.to_dict(include_sensitive=True),
        'expires_in': int(cfg.JWT_EXPIRATION.total_seconds())
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Revoke JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization header'}), 401

    token = auth_header.split(' ')[1]
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    jwt_token = JWTToken.query.filter_by(token_hash=token_hash).first()
    if jwt_token:
        jwt_token.revoked = True
        db.session.commit()

    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/mfa/setup', methods=['POST'])
def mfa_setup():
    """Setup MFA for current user"""
    # Requires authentication
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate MFA secret
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = False  # Not enabled until verified
    db.session.commit()

    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=cfg.MFA_ISSUER
    )

    return jsonify({
        'secret': secret,
        'qr_uri': qr_uri
    })

@auth_bp.route('/mfa/verify', methods=['POST'])
def mfa_verify():
    """Verify and enable MFA"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({'error': 'MFA code required'}), 400

    user = User.query.get(user_id)
    if not user or not user.mfa_secret:
        return jsonify({'error': 'MFA not set up'}), 400

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code):
        return jsonify({'error': 'Invalid MFA code'}), 401

    user.mfa_enabled = True
    db.session.commit()

    return jsonify({'message': 'MFA enabled successfully'})

def generate_jwt(user_id):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + cfg.JWT_EXPIRATION,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')

def get_user_from_token():
    """Extract user ID from JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, cfg.JWT_SECRET, algorithms=['HS256'])

        # Check if token is revoked
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        jwt_token = JWTToken.query.filter_by(token_hash=token_hash, revoked=False).first()

        if not jwt_token:
            return None

        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
