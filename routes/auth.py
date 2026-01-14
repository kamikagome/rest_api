from flask import Blueprint, jsonify, request
from models import db, User
import jwt
import datetime
from config import JWT_SECRET, JWT_EXPIRATION

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """
    POST /auth/register - Create a new user account

    Expected body: {"email": "string", "password": "string"}

    Returns:
        201 Created - User registered successfully
        400 Bad Request - Missing fields or email already exists
    """
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user = User(email=data["email"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict()
    }), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    POST /auth/login - Authenticate and receive JWT token

    Expected body: {"email": "string", "password": "string"}

    Returns:
        200 OK - Login successful, returns JWT token
        401 Unauthorized - Invalid credentials
    """
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = jwt.encode(
        {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200
