from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///noble_innsync.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

    return app
