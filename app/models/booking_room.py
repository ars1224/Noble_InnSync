from app import db
from app.models.types import Money


class BookingRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("booking.id"),
        nullable=False
    )

    room_number = db.Column(db.String(20), nullable=False)
    room_type = db.Column(db.String(100), nullable=False)

    price = db.Column(Money(), nullable=False, default=0)

    adult_capacity = db.Column(db.Integer, nullable=False, default=0)
    child_capacity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<BookingRoom {self.room_number} - {self.room_type}>"
