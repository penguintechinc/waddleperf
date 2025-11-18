"""Organization management routes"""
from flask import Blueprint, jsonify, request
from models import db, OrganizationUnit
from routes.auth import get_user_from_token

orgs_bp = Blueprint('organizations', __name__)

@orgs_bp.route('', methods=['GET'])
def list_organizations():
    """List all organization units"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    orgs = OrganizationUnit.query.all()
    return jsonify({'organizations': [o.to_dict() for o in orgs]})

@orgs_bp.route('/<int:org_id>', methods=['GET'])
def get_organization(org_id):
    """Get organization by ID"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    org = OrganizationUnit.query.get_or_404(org_id)
    return jsonify(org.to_dict())

@orgs_bp.route('', methods=['POST'])
def create_organization():
    """Create new organization"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    if 'name' not in data:
        return jsonify({'error': 'Name required'}), 400

    org = OrganizationUnit(
        name=data['name'],
        description=data.get('description')
    )

    db.session.add(org)
    db.session.commit()

    return jsonify(org.to_dict()), 201
