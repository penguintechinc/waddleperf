"""Statistics query routes"""
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from models import db
from routes.auth import get_user_from_token

stats_bp = Blueprint('statistics', __name__)

@stats_bp.route('/recent', methods=['GET'])
def recent_tests():
    """Get recent test results"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', 100, type=int)

    query = text("""
        SELECT * FROM v_recent_server_tests
        UNION ALL
        SELECT * FROM v_recent_client_tests
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    results = db.session.execute(query, {'limit': limit})

    return jsonify({
        'results': [dict(row._mapping) for row in results]
    })

@stats_bp.route('/device/<device_serial>', methods=['GET'])
def device_stats(device_serial):
    """Get statistics for a specific device"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    query = text("""
        SELECT * FROM v_device_test_stats
        WHERE device_serial = :serial
    """)

    results = db.session.execute(query, {'serial': device_serial})

    return jsonify({
        'device': device_serial,
        'statistics': [dict(row._mapping) for row in results]
    })
