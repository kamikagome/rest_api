from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from models import db

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Cache configuration (simple in-memory cache)
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 5 minutes

# Initialize extensions
db.init_app(app)
cache = Cache(app)

# Rate limiting configuration
# Limits are per IP address by default
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per minute"],  # Global default
    storage_uri="memory://",
)

# Register route blueprints
from routes.tasks import tasks_bp
from routes.auth import auth_bp
app.register_blueprint(tasks_bp)
app.register_blueprint(auth_bp)


@app.route("/")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "message": "TaskFlow API is running"}


# Create database tables when app starts
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
