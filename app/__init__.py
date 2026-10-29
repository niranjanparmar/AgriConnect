import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """Application factory for AgriConnect."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions with app context
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.marketplace import marketplace_bp
    from app.orders import orders_bp
    from app.prices import prices_bp
    from app.errors import errors_bp
    from app.cli import cli_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(prices_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(cli_bp)

    # Ensure upload directory exists
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    return app

