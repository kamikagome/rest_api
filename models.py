from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    """
    User model - represents a user in TaskFlow API

    Security note: We NEVER store plain text passwords.
    bcrypt hashes the password with a random salt.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationship: One user has many tasks
    tasks = db.relationship("Task", backref="owner", lazy=True)

    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        """Verify password against stored hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def to_dict(self):
        """Convert to dictionary (never include password!)."""
        return {
            "id": self.id,
            "email": self.email
        }


class Task(db.Model):
    """
    Task model - represents a task in our TaskFlow API

    Now linked to a user via user_id foreign key.
    """
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    completed = db.Column(db.Boolean, default=False)

    # Foreign key: Each task belongs to a user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        """Convert model to dictionary for JSON response."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "user_id": self.user_id
        }
