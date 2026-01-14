from functools import wraps
from flask import request, jsonify, g
import jwt
from config import JWT_SECRET
from models import User


def token_required(f):
    """
    Decorator to protect routes that require authentication.

    Usage:
        @app.route("/protected")
        @token_required
        def protected_route():
            # Access current user via g.current_user
            return jsonify({"user": g.current_user.email})

    How it works:
        1. Checks for Authorization header with Bearer token
        2. Decodes and validates the JWT
        3. Attaches user to Flask's g object
        4. Returns 401 if token is missing/invalid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")

        if auth_header:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            # Decode the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            # Get the user from database
            current_user = User.query.get(payload["user_id"])

            if not current_user:
                return jsonify({"error": "User not found"}), 401

            # Store user in Flask's g object (request-scoped)
            g.current_user = current_user

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
