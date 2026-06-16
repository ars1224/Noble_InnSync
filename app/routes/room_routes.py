from flask import Blueprint, abort, render_template, request

from flask import Blueprint, render_template, request
from app import db
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
    available_count = Room.query.filter_by(
        room_type=details["room_type"],
        status="Available"
    ).count()

    return {
        "slug": room_slug,
        **details,
        "image": details["images"][0],
        "available_count": available_count,
    }



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
    return f"NIS-2026-{4000 + selected_room.id}"


@room.route("/available-rooms")
def available_rooms():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

    single_room = (
        Room.query
        .filter_by(room_type="Single Room", status="Available")
        .order_by(Room.room_number.asc())
        .first()
    )

    double_room = (
        Room.query
        .filter_by(room_type="Double Room", status="Available")
        .order_by(Room.room_number.asc())
        .first()
    )

    family_room = (
        Room.query
        .filter_by(room_type="Family Room", status="Available")
        .order_by(Room.room_number.asc())
        .first()
    )

    room_summary = [
        build_room_summary(room_slug, details)
        for room_slug, details in ROOM_CATALOG.items()
        {
            "id": single_room.id if single_room else None,
            "room_type": "Single Room",
            "description": "Perfect for solo travelers seeking a cozy and affordable stay.",
            "price": 149,
            "capacity_adults": 1,
            "capacity_children": 0,
            "bed": "1 single bed",
            "available_count": Room.query.filter_by(
                room_type="Single Room",
                status="Available",
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_37_08 PM.png",
        },
        {
            "id": double_room.id if double_room else None,
            "room_type": "Double Room",
            "description": "Ideal for couples with spacious comfort and modern amenities.",
            "price": 229,
            "capacity_adults": 2,
            "capacity_children": 1,
            "bed": "1 queen size bed",
            "available_count": Room.query.filter_by(
                room_type="Double Room",
                status="Available",
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_37_54 PM.png",
        },
        {
            "id": family_room.id if family_room else None,
            "room_type": "Family Room",
            "description": "Designed for families and groups with extra space and comfort.",
            "price": 329,
            "capacity_adults": 4,
            "capacity_children": 2,
            "bed": "2 queen size beds + 1 single bed",
            "available_count": Room.query.filter_by(
                room_type="Family Room",
                status="Available",
            ).count(),
            "image": "ChatGPT Image Jun 2, 2026, 08_38_19 PM.png",
        },
    ]

    search_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children,
        "guest_text": (
        "guest_text": (
            f"{adults} adult{'s' if adults != '1' else ''}, "
            f"{children} child{'ren' if children != '1' else ''}"
        ),
            f"{children} child{'ren' if children != '1' else ''}"
        ),
    }

    return render_template(
        "rooms/available_rooms.html",
        room_summary=room_summary,
        search_summary=search_summary
    )


@room.route("/rooms/<room_slug>")
def room_details(room_slug):
    details = ROOM_CATALOG.get(room_slug)
    if not details:
        abort(404)

    room_summary = build_room_summary(room_slug, details)
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

    try:
        adults_count = max(1, int(adults))
    except (TypeError, ValueError):
        adults_count = 1

    try:
        children_count = max(0, int(children))
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

    fits_guests = (
        adults_count <= room_summary["capacity_adults"]
        and children_count <= room_summary["capacity_children"]
    )

    booking_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults_count,
        "children": children_count,
        "guest_text": (
            f"{adults_count} adult{'s' if adults_count != 1 else ''}, "
            f"{children_count} child{'ren' if children_count != 1 else ''}"
        ),
        "nights": nights,
        "stay_total": stay_total,
        "date_error": date_error,
        "fits_guests": fits_guests,
    }

    return render_template(
        "rooms/room_details.html",
        room=room_summary,
        booking_summary=booking_summary,
        policies=ROOM_POLICIES
    )

        search_summary=search_summary,
    )


@room.route("/rooms/<int:room_id>")
def room_details(room_id):
    selected_room = Room.query.get_or_404(room_id)

    return render_template(
        "rooms/room_details.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.args),
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
    selected_room.status = "Booked"
    db.session.commit()
    return render_template(
        "rooms/booking_confirmation.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
        booking_reference=build_booking_reference(selected_room),
        notification_sent=True,
    )


@room.route("/rooms/<int:room_id>/payment/notification-failed", methods=["POST"])
def payment_notification_failed(room_id):
    selected_room = Room.query.get_or_404(room_id)
    selected_room.status = "Booked"
    db.session.commit()
    return render_template(
        "rooms/booking_confirmation.html",
        room=selected_room,
        details=get_room_details(selected_room),
        booking_summary=build_booking_summary(request.form),
        guest_details=build_guest_details(request.form),
        price_breakdown=build_price_breakdown(selected_room),
        booking_reference=build_booking_reference(selected_room),
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
