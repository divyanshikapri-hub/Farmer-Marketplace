from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db, User
from auth import auth_bp


def create_app(config_class=Config):
    """Application factory for FarmLink Flask backend."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing (CORS) with session cookie support
    CORS(app, supports_credentials=True)

    # Initialize SQLAlchemy database connection
    db.init_app(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Basic service health check."""
        return jsonify({"status": "healthy", "service": "FarmLink API"}), 200

    @app.route("/api/test-db", methods=["GET"])
    def test_db():
        """
        GET /api/test-db
        Fetches all users from MySQL to verify database connectivity.
        Returns a JSON list of users and the total count.
        """
        try:
            users = User.query.all()
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Database connection verified successfully.",
                        "count": len(users),
                        "users": [user.to_dict() for user in users],
                    }
                ),
                200,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Database connection failed.",
                        "error": str(e),
                    }
                ),
                500,
            )

    return app


# Application entry point
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
