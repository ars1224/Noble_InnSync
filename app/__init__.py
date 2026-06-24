import os
import secrets

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _load_secret_key(app):
    """Load a deployment secret or create a private key for local development."""
    configured_secret = os.environ.get("SECRET_KEY")
    if configured_secret:
        return configured_secret

    os.makedirs(app.instance_path, exist_ok=True)
    secret_file = os.path.join(app.instance_path, ".secret_key")

    try:
        with open(secret_file, encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        generated_secret = secrets.token_urlsafe(64)
        with open(secret_file, "x", encoding="utf-8") as file:
            file.write(generated_secret)
        return generated_secret


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = _load_secret_key(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///noble_innsync.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.models.room import Room
    from app.models.booking import Booking
    from app.models.booking_room import BookingRoom
    from app.models.accounting import Accounting
    from app.models.inventory import InventoryItem
    from app.models.equipment import EquipmentIssue
    from app.models.activity_log import ActivityLog
    from app.models.user import User

    from app.routes.main_routes import main
    from app.routes.room_routes import room
    from app.routes.booking_routes import booking
    from app.routes.admin import admin
    from app.routes.auth import auth


    app.register_blueprint(main)
    app.register_blueprint(room)
    app.register_blueprint(booking)
    app.register_blueprint(admin)
    app.register_blueprint(auth)

    from app.commands import create_user_command, list_users_command

    app.cli.add_command(create_user_command)
    app.cli.add_command(list_users_command)

    from app.utils.booking_lifecycle import reconcile_lapsed_bookings

    @app.before_request
    def update_lapsed_bookings():
        if request.endpoint != "static":
            reconcile_lapsed_bookings()

    return app
