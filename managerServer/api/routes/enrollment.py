"""Enrollment secrets routes (FleetDM-style team secrets)"""
from flask import Blueprint, jsonify, request
from models import db, OUEnrollmentSecret, DeviceEnrollment, User, OrganizationUnit, ClientConfig
from routes.auth import get_user_from_token
from datetime import datetime
import random

enrollment_bp = Blueprint('enrollment', __name__)

def require_admin(user_id):
    """Check if user is global_admin or ou_admin"""
    user = User.query.get(user_id)
    if not user or user.role not in ['global_admin', 'ou_admin']:
        return False, user
    return True, user

@enrollment_bp.route('/secrets', methods=['GET'])
def list_secrets():
    """List enrollment secrets (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Global admins see all, OU admins see only their OU
    if user.role == 'global_admin':
        secrets = OUEnrollmentSecret.query.all()
    else:
        secrets = OUEnrollmentSecret.query.filter_by(ou_id=user.ou_id).all()

    return jsonify({
        'secrets': [s.to_dict(include_secret=True) for s in secrets]
    })

@enrollment_bp.route('/secrets/<int:ou_id>', methods=['GET'])
def get_ou_secrets(ou_id):
    """Get enrollment secrets for a specific OU (FleetDM: GET /api/v1/fleet/teams/:id/secrets)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # OU admins can only access their own OU
    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    secrets = OUEnrollmentSecret.query.filter_by(ou_id=ou_id, is_active=True).all()
    ou = OrganizationUnit.query.get_or_404(ou_id)

    return jsonify({
        'ou': ou.to_dict(),
        'secrets': [s.to_dict(include_secret=True) for s in secrets]
    })

@enrollment_bp.route('/secrets/<int:ou_id>', methods=['POST'])
def create_secret(ou_id):
    """Create a new enrollment secret for an OU (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # OU admins can only create for their own OU
    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    # Verify OU exists
    ou = OrganizationUnit.query.get_or_404(ou_id)

    data = request.get_json() or {}
    name = data.get('name', f'{ou.name} Enrollment Secret')

    # Generate new secret
    secret = OUEnrollmentSecret(
        ou_id=ou_id,
        secret=OUEnrollmentSecret.generate_secret(),
        name=name,
        is_active=True,
        created_by=user_id
    )

    db.session.add(secret)
    db.session.commit()

    return jsonify({
        'message': 'Enrollment secret created',
        'secret': secret.to_dict(include_secret=True)
    }), 201

@enrollment_bp.route('/secrets/<int:secret_id>', methods=['DELETE'])
def delete_secret(secret_id):
    """Delete (deactivate) an enrollment secret"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    secret = OUEnrollmentSecret.query.get_or_404(secret_id)

    # OU admins can only delete secrets in their OU
    if user.role == 'ou_admin' and user.ou_id != secret.ou_id:
        return jsonify({'error': 'Access denied'}), 403

    # Soft delete (deactivate)
    secret.is_active = False
    db.session.commit()

    return jsonify({'message': 'Enrollment secret deactivated'})

@enrollment_bp.route('/enroll', methods=['POST'])
def enroll_device():
    """Enroll a device using a secret (public endpoint)"""
    data = request.get_json()

    required_fields = ['secret', 'device_serial', 'device_hostname', 'device_os',
                      'device_os_version', 'client_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Find the secret
    secret = OUEnrollmentSecret.query.filter_by(
        secret=data['secret'],
        is_active=True
    ).first()

    if not secret:
        return jsonify({'error': 'Invalid or inactive enrollment secret'}), 401

    # Check if device is already enrolled (FleetDM: permanent OU assignment)
    existing = DeviceEnrollment.query.filter_by(
        device_serial=data['device_serial']
    ).first()

    if existing:
        # Update metadata but don't change OU
        existing.device_hostname = data['device_hostname']
        existing.device_os = data['device_os']
        existing.device_os_version = data['device_os_version']
        existing.client_version = data.get('client_version')
        existing.last_seen = datetime.utcnow()
        existing.is_active = True
        db.session.commit()

        return jsonify({
            'message': 'Device already enrolled, metadata updated',
            'ou_id': existing.ou_id,
            'device_id': existing.id
        })

    # New enrollment
    device = DeviceEnrollment(
        ou_id=secret.ou_id,
        enrollment_secret_id=secret.id,
        device_serial=data['device_serial'],
        device_hostname=data['device_hostname'],
        device_os=data['device_os'],
        device_os_version=data['device_os_version'],
        client_type=data['client_type'],
        client_version=data.get('client_version'),
        enrolled_ip=request.remote_addr,
        last_seen=datetime.utcnow(),
        is_active=True
    )

    db.session.add(device)
    db.session.commit()

    return jsonify({
        'message': 'Device enrolled successfully',
        'ou_id': device.ou_id,
        'device_id': device.id
    }), 201

@enrollment_bp.route('/devices', methods=['GET'])
def list_devices():
    """List enrolled devices (admin and reporter access)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Filter based on role
    if user.role in ['global_admin', 'global_reporter']:
        devices = DeviceEnrollment.query.filter_by(is_active=True).all()
    elif user.role in ['ou_admin', 'ou_reporter']:
        devices = DeviceEnrollment.query.filter_by(ou_id=user.ou_id, is_active=True).all()
    else:
        return jsonify({'error': 'Insufficient permissions'}), 403

    return jsonify({
        'devices': [d.to_dict() for d in devices]
    })

@enrollment_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get device details"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    device = DeviceEnrollment.query.get_or_404(device_id)

    # OU admins/reporters can only see devices in their OU
    if user.role in ['ou_admin', 'ou_reporter'] and user.ou_id != device.ou_id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify(device.to_dict())

@enrollment_bp.route('/devices/<int:device_id>/heartbeat', methods=['POST'])
def device_heartbeat(device_id):
    """Update device last_seen timestamp"""
    device = DeviceEnrollment.query.get_or_404(device_id)
    device.last_seen = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Heartbeat recorded'})

# ============================================
# Client Configuration Endpoints
# ============================================

@enrollment_bp.route('/config', methods=['GET'])
def get_client_config():
    """Get client configuration for enrolled device (used by clients on check-in)"""
    # This can be called with device_serial or by authenticated user
    device_serial = request.args.get('device_serial')

    if device_serial:
        device = DeviceEnrollment.query.filter_by(device_serial=device_serial).first()
        if not device:
            return jsonify({'error': 'Device not enrolled'}), 404
        ou_id = device.ou_id
    else:
        user_id = get_user_from_token()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(user_id)
        ou_id = user.ou_id

    # Get OU-specific config or fall back to default
    config = ClientConfig.query.filter_by(ou_id=ou_id).first()
    if not config:
        config = ClientConfig.query.filter_by(is_default=True).first()

    if not config:
        return jsonify({'error': 'No configuration available'}), 404

    # Calculate actual schedule with random offset
    config_data = config.config_data.copy()
    if 'schedule' in config_data:
        base_interval = config_data['schedule'].get('interval_seconds', 300)
        offset_percent = config_data['schedule'].get('offset_percent', 15)

        # Apply random offset: +/- offset_percent%
        offset_range = base_interval * (offset_percent / 100.0)
        actual_offset = random.uniform(-offset_range, offset_range)
        actual_interval = int(base_interval + actual_offset)

        config_data['schedule']['actual_interval_seconds'] = actual_interval
        config_data['schedule']['next_check_in'] = datetime.utcnow().timestamp() + actual_interval

    # Get client check-in interval (how often to pull config from manager)
    from models import SystemConfig
    checkin_min = SystemConfig.query.filter_by(config_key='client_checkin_min_seconds').first()
    checkin_max = SystemConfig.query.filter_by(config_key='client_checkin_max_seconds').first()

    checkin_min_val = int(checkin_min.config_value) if checkin_min else 1800  # 30 minutes
    checkin_max_val = int(checkin_max.config_value) if checkin_max else 3600  # 60 minutes

    # Random check-in interval between min and max
    next_checkin_seconds = random.randint(checkin_min_val, checkin_max_val)

    return jsonify({
        'config': config_data,
        'config_name': config.config_name,
        'ou_id': config.ou_id,
        'next_checkin_seconds': next_checkin_seconds,  # When to check for config updates
        'next_checkin_at': datetime.utcnow().timestamp() + next_checkin_seconds
    })

@enrollment_bp.route('/configs', methods=['GET'])
def list_client_configs():
    """List all client configurations (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Global admins see all, OU admins see only their OU + default
    if user.role == 'global_admin':
        configs = ClientConfig.query.all()
    else:
        configs = ClientConfig.query.filter(
            db.or_(
                ClientConfig.ou_id == user.ou_id,
                ClientConfig.is_default == True
            )
        ).all()

    return jsonify({
        'configs': [c.to_dict() for c in configs]
    })

@enrollment_bp.route('/configs/<int:ou_id>', methods=['GET'])
def get_ou_config(ou_id):
    """Get configuration for a specific OU"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # OU admins can only access their own OU
    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    config = ClientConfig.query.filter_by(ou_id=ou_id).first()
    if not config:
        # Return default config
        config = ClientConfig.query.filter_by(is_default=True).first()

    if not config:
        return jsonify({'error': 'No configuration found'}), 404

    return jsonify(config.to_dict())

@enrollment_bp.route('/configs/<int:ou_id>', methods=['PUT'])
def update_ou_config(ou_id):
    """Update or create configuration for an OU (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # OU admins can only update their own OU
    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data or 'config_data' not in data:
        return jsonify({'error': 'config_data required'}), 400

    # Verify OU exists
    ou = OrganizationUnit.query.get_or_404(ou_id)

    # Find or create config
    config = ClientConfig.query.filter_by(ou_id=ou_id).first()
    if not config:
        config = ClientConfig(
            ou_id=ou_id,
            user_id=user_id,
            config_name=data.get('config_name', f'{ou.name} Configuration'),
            config_data=data['config_data'],
            is_default=False
        )
        db.session.add(config)
    else:
        config.config_data = data['config_data']
        if 'config_name' in data:
            config.config_name = data['config_name']
        config.user_id = user_id

    db.session.commit()

    return jsonify({
        'message': 'Configuration updated',
        'config': config.to_dict()
    })

@enrollment_bp.route('/configs/default', methods=['GET'])
def get_default_config():
    """Get the default configuration"""
    config = ClientConfig.query.filter_by(is_default=True).first()
    if not config:
        return jsonify({'error': 'No default configuration found'}), 404

    return jsonify(config.to_dict())

@enrollment_bp.route('/configs/default', methods=['PUT'])
def update_default_config():
    """Update the default configuration (global admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user or user.role != 'global_admin':
        return jsonify({'error': 'Global admin access required'}), 403

    data = request.get_json()
    if not data or 'config_data' not in data:
        return jsonify({'error': 'config_data required'}), 400

    config = ClientConfig.query.filter_by(is_default=True).first()
    if not config:
        return jsonify({'error': 'Default configuration not found'}), 404

    config.config_data = data['config_data']
    if 'config_name' in data:
        config.config_name = data['config_name']
    config.user_id = user_id

    db.session.commit()

    return jsonify({
        'message': 'Default configuration updated',
        'config': config.to_dict()
    })
