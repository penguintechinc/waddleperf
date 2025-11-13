"""System configuration routes (FleetDM-style)"""
from flask import Blueprint, jsonify, request
from models import db, SystemConfig, User
from routes.auth import get_user_from_token
import json

config_bp = Blueprint('config', __name__)

def require_admin(user_id):
    """Check if user is global_admin"""
    user = User.query.get(user_id)
    if not user or user.role != 'global_admin':
        return False
    return True

@config_bp.route('', methods=['GET'])
def get_all_config():
    """Get all system configuration (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    configs = SystemConfig.query.all()
    config_dict = {}
    for config in configs:
        value = config.config_value
        # Parse JSON values
        if config.config_type == 'json' and value:
            try:
                value = json.loads(value)
            except:
                pass
        elif config.config_type == 'boolean':
            value = value.lower() == 'true' if value else False
        elif config.config_type == 'integer':
            value = int(value) if value else 0

        config_dict[config.config_key] = {
            'value': value,
            'type': config.config_type,
            'description': config.description,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None
        }

    return jsonify({'config': config_dict})

@config_bp.route('/<key>', methods=['GET'])
def get_config(key):
    """Get a specific configuration value"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    config = SystemConfig.query.filter_by(config_key=key).first()
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404

    value = config.config_value
    if config.config_type == 'json' and value:
        try:
            value = json.loads(value)
        except:
            pass
    elif config.config_type == 'boolean':
        value = value.lower() == 'true' if value else False
    elif config.config_type == 'integer':
        value = int(value) if value else 0

    return jsonify({
        'config_key': config.config_key,
        'value': value,
        'type': config.config_type,
        'description': config.description
    })

@config_bp.route('', methods=['PATCH'])
def update_config():
    """Update system configuration (admin only, FleetDM-style bulk update)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updated = []
    errors = []

    for key, value in data.items():
        config = SystemConfig.query.filter_by(config_key=key).first()
        if not config:
            errors.append(f'Configuration key "{key}" not found')
            continue

        # Convert value to string for storage
        if config.config_type == 'json':
            config.config_value = json.dumps(value)
        elif config.config_type == 'boolean':
            config.config_value = 'true' if value else 'false'
        else:
            config.config_value = str(value)

        config.updated_by = user_id
        updated.append(key)

    if updated:
        db.session.commit()

    return jsonify({
        'updated': updated,
        'errors': errors
    })

@config_bp.route('/<key>', methods=['PUT'])
def set_config(key):
    """Set a specific configuration value (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if 'value' not in data:
        return jsonify({'error': 'Value required'}), 400

    config = SystemConfig.query.filter_by(config_key=key).first()
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404

    value = data['value']

    # Convert value to string for storage
    if config.config_type == 'json':
        config.config_value = json.dumps(value)
    elif config.config_type == 'boolean':
        config.config_value = 'true' if value else 'false'
    else:
        config.config_value = str(value)

    config.updated_by = user_id
    db.session.commit()

    return jsonify({
        'config_key': config.config_key,
        'value': value,
        'updated': True
    })
