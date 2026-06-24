from datetime import date

from app import db
from app.models.booking import Booking
from app.models.room import Room


INACTIVE_BOOKING_STATUSES = {"Cancelled", "Checked Out"}
CARD_PAYMENT_METHODS = {"card", "card payment"}


def _checkout_date(booking):
    if isinstance(booking.check_out, date):
        return booking.check_out
    try:
        return date.fromisoformat(booking.check_out)
    except (TypeError, ValueError):
        return None


def reconcile_lapsed_bookings(today=None):
    """Cancel lapsed unpaid/pay-on-arrival bookings and release rooms. Paid card bookings are kept."""
    today = today or date.today()
    bookings = Booking.query.all()
    bookings_with_checkout = [
        (booking, _checkout_date(booking))
        for booking in bookings
    ]

    lapsed_bookings = [
        booking
        for booking, checkout in bookings_with_checkout
        if booking.status not in INACTIVE_BOOKING_STATUSES
        and checkout
        and checkout < today
    ]

    if not lapsed_bookings:
        return 0

    bookings_to_cancel = []

    for booking in lapsed_bookings:
        has_paid_card_payment = any(
            payment.payment_status == "Paid"
            and (payment.payment_method or "").strip().lower() in CARD_PAYMENT_METHODS
            for payment in booking.accounting
        )

        if has_paid_card_payment:
            booking.status = "Confirmed"
            continue

        bookings_to_cancel.append(booking)

    if not bookings_to_cancel:
        db.session.commit()
        return 0

    cancelled_ids = {booking.id for booking in bookings_to_cancel}

    active_room_numbers = {
        booked_room.room_number
        for booking, checkout in bookings_with_checkout
        if booking.id not in cancelled_ids
        and booking.status not in INACTIVE_BOOKING_STATUSES
        and (checkout is None or checkout >= today)
        for booked_room in booking.booking_rooms
    }

    rooms_to_release = {
        booked_room.room_number
        for booking in bookings_to_cancel
        for booked_room in booking.booking_rooms
    } - active_room_numbers

    for booking in bookings_to_cancel:
        booking.status = "Cancelled"

    if rooms_to_release:
        rooms = Room.query.filter(Room.room_number.in_(rooms_to_release)).all()
        for room in rooms:
            if room.status != "Maintenance":
                room.status = "Available"

    db.session.commit()
    return len(bookings_to_cancel)