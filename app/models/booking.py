from app import db
from app.models.types import ISODate, Money, utc_now


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reference_number = db.Column(db.String(30), nullable=False, unique=True)

    guest_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)

    check_in = db.Column(ISODate(), nullable=False)
    check_out = db.Column(ISODate(), nullable=False)

    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, nullable=False, default=0)

    total_price = db.Column(Money(), nullable=False, default=0)

    status = db.Column(db.String(50), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, default=utc_now)

    booking_rooms = db.relationship(
        "BookingRoom",
        backref="booking",
        lazy=True,
        cascade="all, delete-orphan"
    )

    accounting = db.relationship(
        "Accounting",
        backref="booking",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Booking {self.reference_number}>"
