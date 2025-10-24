"""
Authentication and authorization
"""

from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import db


def token_required(f):
    """Decorator to require JWT token for endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            return f(current_user=current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token', 'message': str(e)}), 401

    return decorated


def validate_login(username: str, password: str) -> bool:
    """Validate user credentials"""
    return db.verify_password(username, password)
