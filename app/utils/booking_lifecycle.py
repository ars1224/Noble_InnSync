from datetime import date

from app import db
from app.models.booking import Booking
from app.models.room import Room


INACTIVE_BOOKING_STATUSES = {"Cancelled", "Checked Out"}
CARD_PAYMENT_METHODS = {"card", "card payment"}


def _checkout_date(booking):
    try:
        return date.fromisoformat(booking.check_out)
    except (TypeError, ValueError):
        return None


def reconcile_lapsed_bookings(today=None):
    """Cancel active bookings that have passed checkout and refund paid cards."""
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

    lapsed_ids = {booking.id for booking in lapsed_bookings}
    active_room_numbers = {
        booked_room.room_number
        for booking, checkout in bookings_with_checkout
        if booking.id not in lapsed_ids
        and booking.status not in INACTIVE_BOOKING_STATUSES
        and (checkout is None or checkout >= today)
        for booked_room in booking.booking_rooms
    }
    rooms_to_release = {
        booked_room.room_number
        for booking in lapsed_bookings
        for booked_room in booking.booking_rooms
    } - active_room_numbers

    for booking in lapsed_bookings:
        booking.status = "Cancelled"

        for payment in booking.accounting:
            if (
                payment.payment_status == "Paid"
                and (
                    (payment.payment_method or "").strip().lower()
                    in CARD_PAYMENT_METHODS
                )
            ):
                payment.payment_status = "Refunded"

    if rooms_to_release:
        rooms = Room.query.filter(Room.room_number.in_(rooms_to_release)).all()
        for room in rooms:
            if room.status != "Maintenance":
                room.status = "Available"

    db.session.commit()
    return len(lapsed_bookings)
