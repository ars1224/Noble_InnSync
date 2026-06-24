from app import db
from app.models.types import ISODate, Money, utc_now


class Accounting(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    transaction_no = db.Column(db.String(30), nullable=False, unique=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("booking.id"),
        nullable=False
    )

    check_in = db.Column(ISODate(), nullable=False)
    check_out = db.Column(ISODate(), nullable=False)

    total_price = db.Column(Money(), nullable=False, default=0)

    payment_status = db.Column(db.String(50), nullable=False, default="Unpaid")
    payment_method = db.Column(db.String(50), nullable=False, default="Pay on Arrival")

    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Accounting {self.transaction_no}>"
