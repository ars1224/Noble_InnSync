from flask import Blueprint, redirect, render_template, request, url_for
from app.models.booking import Booking
from app.models.room import Room
from app.utils.reservations import authorize_reservation

main = Blueprint("main", __name__)

@main.route("/")
def home():

    room_summary = [

       {
            "room_type": "Single Room",
            "description": "Perfect for solo travelers seeking a cozy and affordable stay.",
            "price": 149,
            "capacity_adults": 1,
            "capacity_children": 0,
            "bed": "1 single bed",
            "available_count": Room.query.filter_by(
                room_type="Single Room",
                status="Available"
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_37_08 PM.png"
        },
        {
            "room_type": "Double Room",
            "description": "Ideal for couples with spacious comfort and modern amenities.",
            "price": 229,
            "capacity_adults": 2,
            "capacity_children": 1,
            "bed": "1 queen size bed",
            "available_count": Room.query.filter_by(
                room_type="Double Room",
                status="Available"
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_37_54 PM.png"
        },
        {
            "room_type": "Family Room",
            "description": "Designed for families and groups with extra space and comfort.",
            "price": 329,
            "capacity_adults": 4,
            "capacity_children": 2,
            "bed": "2 queen size beds + 1 single bed",
            "available_count": Room.query.filter_by(
                room_type="Family Room",
                status="Available"
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_38_19 PM.png"
        }

    ]

    return render_template(
        "index.html",
        room_summary=room_summary
    )


@main.route("/login")
def login_selection():
    return redirect(url_for("auth.staff_login"))


@main.route("/reservation-status")
def reservation_status():
    reference_number = request.args.get("reference_number", "").strip()
    guest_name = request.args.get("guest_name", "").strip()
    searched = bool(reference_number or guest_name)
    booking = None

    if reference_number and guest_name:
        booking = Booking.query.filter(
            Booking.reference_number.ilike(reference_number),
            Booking.guest_name.ilike(guest_name),
        ).first()

        if booking:
            authorize_reservation(booking.reference_number)

    payment = booking.accounting[0] if booking and booking.accounting else None

    return render_template(
        "bookings/reservation_status.html",
        booking=booking,
        payment=payment,
        reference_number=reference_number,
        guest_name=guest_name,
        searched=searched,
    )
