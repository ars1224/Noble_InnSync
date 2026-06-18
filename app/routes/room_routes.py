from flask import Blueprint, abort, render_template, request
from app import db
from app.models.accounting import Accounting
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.room import Room
from app.utils.pricing import calculate_stay_total


room = Blueprint("room", __name__)


ROOM_CATALOG = {
    "single-room": {
        "room_type": "Single Room",
        "title": "A quiet, comfortable stay for one",
        "description": (
            "A thoughtfully arranged room for solo travellers, short business "
            "stays, and guests who value privacy and simplicity."
        ),
        "price": 149,
        "capacity_adults": 1,
        "capacity_children": 0,
        "bed": "1 single bed",
        "size": "18 m²",
        "images": [
            "ChatGPT Image Jun 2, 2026, 08_37_08 PM.png", "single1.png", "single2.png"
        ],
        "amenities": [
            "Free Wi-Fi",
            "Private bathroom",
            "Work desk",
            "Air conditioning",
            "Flat-screen TV",
            "Daily housekeeping",
            "Complimentary breakfast",
        ],
        "highlights": [
            "Ideal for one guest",
            "Dedicated work area",
            "Quiet room layout",
        ],
    },
    "double-room": {
        "room_type": "Double Room",
        "title": "Modern comfort with room to unwind",
        "description": (
            "A spacious room for couples or small parties, combining a generous "
            "sleeping area with practical amenities for a relaxed stay."
        ),
        "price": 229,
        "capacity_adults": 2,
        "capacity_children": 1,
        "bed": "1 queen-size bed",
        "size": "26 m²",
        "images": [
            "ChatGPT Image Jun 2, 2026, 08_37_54 PM.png", "double1.png", "double2.png", "double3.png"
        ],
        "amenities": [
            "Free Wi-Fi",
            "Private bathroom",
            "Queen-size bed",
            "Air conditioning",
            "Flat-screen TV",
            "Tea and coffee station",
            "Daily housekeeping",
            "Complimentary breakfast",
        ],
        "highlights": [
            "Comfortable for couples",
            "Extra seating area",
            "Generous storage space",
        ],
    },
    "family-room": {
        "room_type": "Family Room",
        "title": "Flexible space for families and groups",
        "description": (
            "Our largest room option gives families and groups the space, beds, "
            "and everyday conveniences needed for a comfortable shared stay."
        ),
        "price": 329,
        "capacity_adults": 4,
        "capacity_children": 2,
        "bed": "2 queen-size beds and 1 single bed",
        "size": "38 m²",
        "images": [
            "ChatGPT Image Jun 2, 2026, 08_38_19 PM.png", "fam1.png", "fam2.png", "fam3.png"
        ],
        "amenities": [
            "Free Wi-Fi",
            "Large private bathroom",
            "Multiple beds",
            "Air conditioning",
            "Flat-screen TV",
            "Mini refrigerator",
            "Tea and coffee station",
            "Daily housekeeping",
            "Complimentary breakfast",
        ],
        "highlights": [
            "Sleeps up to six guests",
            "Flexible family layout",
            "Extra luggage storage",
        ],
    },
}


ROOM_POLICIES = [
    "Check-in is available from 2:00 PM.",
    "Check-out is required by 10:00 AM.",
    "A valid photo ID is required at check-in.",
    "Smoking is not permitted inside guest rooms.",
    "Please contact reception in advance for accessibility requirements.",
]


def build_room_summary(room_slug, details):
    return build_room_summary_for_dates(room_slug, details, "", "")


def booking_overlaps(booking, check_in, check_out):
    return (
        booking.check_in < check_out
        and booking.check_out > check_in
        and booking.status not in ["Cancelled", "Checked Out"]
    )


def booked_room_numbers_for_dates(check_in, check_out):
    if not check_in or not check_out:
        return set()

    bookings = Booking.query.all()

    return {
        booked_room.room_number
        for booking in bookings
        if booking_overlaps(booking, check_in, check_out)
        for booked_room in booking.booking_rooms
    }


def build_room_summary_for_dates(room_slug, details, check_in, check_out):
    candidate_rooms = (
        Room.query
        .filter(
            Room.room_type == details["room_type"],
            Room.status != "Maintenance"
        )
        .order_by(Room.room_number.asc())
        .all()
    )
    booked_room_numbers = booked_room_numbers_for_dates(check_in, check_out)

    if check_in and check_out:
        available_rooms = [
            room for room in candidate_rooms
            if room.room_number not in booked_room_numbers
        ]
    else:
        available_rooms = [
            room for room in candidate_rooms
            if room.status == "Available"
        ]

    first_available_room = available_rooms[0] if available_rooms else None
    display_room = first_available_room or (candidate_rooms[0] if candidate_rooms else None)
    available_count = len(available_rooms)

    return {
        "id": display_room.id if display_room else None,
        "slug": room_slug,
        "status": first_available_room.status if first_available_room else "Unavailable",
        **details,
        "image": details["images"][0],
        "available_count": available_count,
    }


def build_room_detail_summary(selected_room):
    room_slug = next(
        (
            slug for slug, details in ROOM_CATALOG.items()
            if details["room_type"] == selected_room.room_type
        ),
        None
    )
    if not room_slug:
        abort(404)

    room_summary = build_room_summary_for_dates(
        room_slug,
        ROOM_CATALOG[room_slug],
        request.args.get("check_in", ""),
        request.args.get("check_out", "")
    )
    room_summary["id"] = selected_room.id
    room_summary["status"] = selected_room.status
    return room_summary



def get_room_details(selected_room):
    room_images = {
        "Single Room": "ChatGPT Image Jun 2, 2026, 08_37_08 PM.png",
        "Double Room": "ChatGPT Image Jun 2, 2026, 08_37_54 PM.png",
        "Family Room": "ChatGPT Image Jun 2, 2026, 08_38_19 PM.png",
    }
    return {
        "title": selected_room.room_type,
        "description": selected_room.description,
        "capacity": "See room capacity",
        "bed": "Bed included",
        "image": room_images.get(selected_room.room_type, "BCO.4a342cff-d6f3-4296-b81d-efc5c1fab770.png"),
        "amenities": ["Wi-Fi", "Air conditioning", "Private bathroom"],
        "rules": [
            "Check-in: 2:00 PM",
            "Check-out: 12:00 PM",
            "No smoking inside the room",
        ],
    }


def build_booking_summary(source):
    summary = {
        "check_in": source.get("check_in", ""),
        "check_out": source.get("check_out", ""),
        "adults": source.get("adults", "1"),
        "children": source.get("children", "0"),
        "room_type": source.get("room_type", ""),
        "max_price": source.get("max_price", ""),
        "sort_by": source.get("sort_by", "lowest_price"),
    }
    summary["guest_text"] = (
        f"{summary['adults']} adult{'s' if summary['adults'] != '1' else ''}, "
        f"{summary['children']} child{'ren' if summary['children'] != '1' else ''}"
    )
    return summary


def build_room_booking_summary(room_summary, source):
    check_in = source.get("check_in", "")
    check_out = source.get("check_out", "")

    try:
        adults_count = max(1, int(source.get("adults", "1")))
    except (TypeError, ValueError):
        adults_count = 1

    try:
        children_count = max(0, int(source.get("children", "0")))
    except (TypeError, ValueError):
        children_count = 0

    nights = None
    stay_total = None
    date_error = None

    if check_in and check_out:
        try:
            nights, stay_total = calculate_stay_total(
                room_summary["price"],
                check_in,
                check_out
            )
        except ValueError as error:
            date_error = str(error)

    return {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults_count,
        "children": children_count,
        "room_type": source.get("room_type", ""),
        "max_price": source.get("max_price", ""),
        "sort_by": source.get("sort_by", "lowest_price"),
        "guest_text": (
            f"{adults_count} adult{'s' if adults_count != 1 else ''}, "
            f"{children_count} child{'ren' if children_count != 1 else ''}"
        ),
        "nights": nights,
        "stay_total": stay_total,
        "date_error": date_error,
        "fits_guests": (
            adults_count <= room_summary["capacity_adults"]
            and children_count <= room_summary["capacity_children"]
        ),
    }


def build_guest_details(source):
    return {
        "first_name": source.get("first_name", ""),
        "last_name": source.get("last_name", ""),
        "email": source.get("email", ""),
        "phone": source.get("phone", ""),
        "requests": source.get("requests", ""),
    }


def build_price_breakdown(selected_room):
    nights = 2
    room_total = selected_room.price * nights
    tax_total = room_total * 0.15
    return {
        "nights": nights,
        "room_total": room_total,
        "tax_total": tax_total,
        "total": room_total + tax_total,
    }


def build_temp_booking_id(selected_room):
    return f"TEMP-{2000 + selected_room.id}"


def build_booking_reference(selected_room):
    base_reference = f"NIS-2026-{4000 + selected_room.id}"

    if not Booking.query.filter_by(reference_number=base_reference).first():
        return base_reference

    counter = 2
    while Booking.query.filter_by(reference_number=f"{base_reference}-{counter}").first():
        counter += 1

    return f"{base_reference}-{counter}"


def save_confirmed_booking(selected_room, form_source, booking_reference):
    guest_details = build_guest_details(form_source)
    booking_summary = build_booking_summary(form_source)
    price_breakdown = build_price_breakdown(selected_room)
    guest_name = (
        f"{guest_details['first_name']} {guest_details['last_name']}"
    ).strip() or "Guest"

    booking = Booking(
        reference_number=booking_reference,
        guest_name=guest_name,
        email=guest_details["email"] or "guest@example.com",
        phone=guest_details["phone"] or "Not provided",
        check_in=booking_summary["check_in"],
        check_out=booking_summary["check_out"],
        adults=int(booking_summary["adults"]),
        children=int(booking_summary["children"]),
        total_price=price_breakdown["total"],
        status="Confirmed",
    )

    db.session.add(booking)
    db.session.flush()

    db.session.add(BookingRoom(
        booking_id=booking.id,
        room_number=selected_room.room_number,
        room_type=selected_room.room_type,
        price=selected_room.price,
        adult_capacity=booking.adults,
        child_capacity=booking.children,
    ))

    db.session.add(Accounting(
        transaction_no=f"TXN-{booking_reference}",
        booking_id=booking.id,
        check_in=booking.check_in,
        check_out=booking.check_out,
        total_price=booking.total_price,
        payment_status="Paid",
        payment_method="Card",
    ))

    return booking


@room.route("/available-rooms")
def available_rooms():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

    room_summary = [
        build_room_summary_for_dates(room_slug, details, check_in, check_out)
        for room_slug, details in ROOM_CATALOG.items()
    ]

    search_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children,
        "guest_text": (
            f"{adults} adult{'s' if adults != '1' else ''}, "
            f"{children} child{'ren' if children != '1' else ''}"
        ),
    }

    return render_template(
        "rooms/available_rooms.html",
        room_summary=room_summary,
        search_summary=search_summary
    )


@room.route("/rooms/<room_slug>")
def room_type_details(room_slug):
    details = ROOM_CATALOG.get(room_slug)
    if not details:
        abort(404)

    room_summary = build_room_summary_for_dates(
        room_slug,
        details,
        request.args.get("check_in", ""),
        request.args.get("check_out", "")
    )
    booking_summary = build_room_booking_summary(room_summary, request.args)

    return render_template(
        "rooms/room_details.html",
        room=room_summary,
        booking_summary=booking_summary,
        policies=ROOM_POLICIES
    )

@room.route("/rooms/<int:room_id>")
def room_details(room_id):
    selected_room = Room.query.get_or_404(room_id)
    room_summary = build_room_detail_summary(selected_room)
    booking_summary = build_room_booking_summary(room_summary, request.args)

    return render_template(
        "rooms/room_details.html",
        room=room_summary,
        booking_summary=booking_summary,
        policies=ROOM_POLICIES,
    )


@room.route("/rooms/<int:room_id>/book")
def booking_form(room_id):
    selected_room = Room.query.get_or_404(room_id)

    return render_template(
        "rooms/booking_form.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.args),
    )


@room.route("/rooms/<int:room_id>/review", methods=["POST"])
def booking_review(room_id):
    selected_room = Room.query.get_or_404(room_id)
    return render_template(
        "rooms/booking_review.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
    )


@room.route("/rooms/<int:room_id>/hold", methods=["POST"])
def temporary_booking_hold(room_id):
    selected_room = Room.query.get_or_404(room_id)
    hold_created = selected_room.status == "Available"
    if hold_created:
        selected_room.status = "On Hold"
        db.session.commit()

    return render_template(
        "rooms/payment.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
        temp_booking_id=build_temp_booking_id(selected_room),
        hold_created=hold_created,
    )


@room.route("/rooms/<int:room_id>/payment/success", methods=["POST"])
def payment_success(room_id):
    selected_room = Room.query.get_or_404(room_id)
    booking_reference = build_booking_reference(selected_room)
    save_confirmed_booking(selected_room, request.form, booking_reference)
    selected_room.status = "Booked"
    db.session.commit()
    return render_template(
        "rooms/booking_confirmation.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
        booking_reference=booking_reference,
        notification_sent=True,
    )


@room.route("/rooms/<int:room_id>/payment/notification-failed", methods=["POST"])
def payment_notification_failed(room_id):
    selected_room = Room.query.get_or_404(room_id)
    booking_reference = build_booking_reference(selected_room)
    save_confirmed_booking(selected_room, request.form, booking_reference)
    selected_room.status = "Booked"
    db.session.commit()
    return render_template(
        "rooms/booking_confirmation.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
        booking_reference=booking_reference,
        notification_sent=False,
    )


def render_payment_result(room_id, payment_status):
    selected_room = Room.query.get_or_404(room_id)
    return render_template(
        "rooms/payment_result.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form or request.args),
        guest_details=build_guest_details(request.form or request.args),
        price_breakdown=build_price_breakdown(selected_room),
        temp_booking_id=request.values.get(
            "temp_booking_id", build_temp_booking_id(selected_room)
        ),
        payment_status=payment_status,
    )


@room.route("/rooms/<int:room_id>/payment/failed", methods=["POST"])
def payment_failed(room_id):
    return render_payment_result(room_id, "failed")


@room.route("/rooms/<int:room_id>/payment/pending", methods=["POST"])
def payment_pending(room_id):
    return render_payment_result(room_id, "pending")
