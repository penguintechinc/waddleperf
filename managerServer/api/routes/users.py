"""User management routes"""
from flask import Blueprint, request, jsonify
from models import db, User
from routes.auth import get_user_from_token

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
def list_users():
    """List all users (with pagination)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    users = User.query.paginate(page=page, per_page=per_page)

    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'page': page,
        'per_page': per_page
    })

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    include_sensitive = (requester_id == user_id)

    return jsonify(user.to_dict(include_sensitive=include_sensitive))

@users_bp.route('', methods=['POST'])
def create_user():
    """Create new user"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # Validate required fields
    required = ['username', 'email', 'password']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if username/email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user'),
        ou_id=data.get('ou_id'),
        api_key=User.generate_api_key()
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict(include_sensitive=True)), 201

@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # Update allowed fields
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'ou_id' in data:
        user.ou_id = data['ou_id']
    if 'is_active' in data:
        user.is_active = data['is_active']

    db.session.commit()
    return jsonify(user.to_dict())

@users_bp.route('/<int:user_id>/password', methods=['PUT'])
def change_password(user_id):
    """Change user password"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'password' not in data:
        return jsonify({'error': 'Password required'}), 400

    user.set_password(data['password'])
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'})

@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'})
