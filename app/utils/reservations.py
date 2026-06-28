import secrets
from datetime import date

from flask import session
from sqlalchemy import select, text

from app import db
from app.models.booking import Booking
from app.models.room import Room


ACTIVE_STATUSES = {"Pending", "Confirmed", "Checked In"}
AUTHORIZED_RESERVATIONS_KEY = "authorized_reservations"
REFERENCE_NUMBER_DIGITS = 6


def as_date(value):
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def booking_overlaps(booking, check_in, check_out):
    requested_check_in = as_date(check_in)
    requested_check_out = as_date(check_out)
    booking_check_in = as_date(booking.check_in)
    booking_check_out = as_date(booking.check_out)

    return bool(
        requested_check_in
        and requested_check_out
        and booking_check_in
        and booking_check_out
        and booking_check_in < requested_check_out
        and booking_check_out > requested_check_in
        and booking.status in ACTIVE_STATUSES
    )


def booked_room_numbers_for_dates(check_in, check_out):
    if not as_date(check_in) or not as_date(check_out):
        return set()

    return {
        booked_room.room_number
        for booking in Booking.query.all()
        if booking_overlaps(booking, check_in, check_out)
        for booked_room in booking.booking_rooms
    }


def begin_booking_transaction():
    """Serialize room allocation so availability is rechecked under a lock."""
    if db.engine.dialect.name == "sqlite":
        session = db.session()
        if session.in_transaction():
            if session.new or session.dirty or session.deleted:
                raise RuntimeError(
                    "Booking lock must be acquired before changing database state."
                )
            session.rollback()
        db.session.execute(text("BEGIN IMMEDIATE"))
        return

    db.session.execute(select(Room.id).with_for_update()).all()


def _unique_token(prefix, model, field_name):
    while True:
        value = f"{prefix}-{secrets.token_urlsafe(18)}"
        field = getattr(model, field_name)
        if not db.session.execute(select(field).where(field == value)).first():
            return value


def _unique_numeric_reference(prefix, model, field_name):
    field = getattr(model, field_name)
    lower_bound = 10 ** (REFERENCE_NUMBER_DIGITS - 1)
    range_size = 9 * lower_bound

    while True:
        number = secrets.randbelow(range_size) + lower_bound
        value = f"{prefix}{number}"
        if not db.session.execute(select(field).where(field == value)).first():
            return value


def generate_reference_number(prefix="NIS"):
    return _unique_numeric_reference(prefix, Booking, "reference_number")


def generate_transaction_number(prefix="TXN"):
    from app.models.accounting import Accounting

    return _unique_token(prefix, Accounting, "transaction_no")


def authorize_reservation(reference_number):
    authorized = list(session.get(AUTHORIZED_RESERVATIONS_KEY, []))
    if reference_number not in authorized:
        authorized.append(reference_number)
    session[AUTHORIZED_RESERVATIONS_KEY] = authorized[-10:]


def reservation_is_authorized(reference_number):
    return reference_number in session.get(AUTHORIZED_RESERVATIONS_KEY, [])
