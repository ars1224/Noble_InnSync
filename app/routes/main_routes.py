from flask import Blueprint, render_template, request
from sqlalchemy import func
from app import db
from app.models.room import Room

main = Blueprint("main", __name__)

ROOM_DETAILS = {
    "Single Room": {
        "title": "Single Room",
        "description": "A calm, compact room designed for solo guests, short stays, and quiet rest after a full day.",
        "capacity": "1 guest",
        "bed": "1 single bed",
        "amenities": ["Wi-Fi", "Aircon", "Private bath", "Desk"],
        "rules": ["Check-in: 2:00 PM", "Check-out: 12:00 PM", "No smoking inside room"],
    },
    "Double Room": {
        "title": "Double Room",
        "description": "A comfortable room for two guests with more space to settle in and relax between plans.",
        "capacity": "2 guests",
        "bed": "1 double bed",
        "amenities": ["Wi-Fi", "Aircon", "Private bath", "TV"],
        "rules": ["Check-in: 2:00 PM", "Check-out: 12:00 PM", "No smoking inside room"],
    },
    "Family Room": {
        "title": "Family Room",
        "description": "A spacious family-friendly room with flexible sleeping space and practical comfort for group stays.",
        "capacity": "4 guests",
        "bed": "2 double beds",
        "amenities": ["Wi-Fi", "Aircon", "Private bath", "TV", "Family space"],
        "rules": ["Check-in: 2:00 PM", "Check-out: 12:00 PM", "No smoking inside room"],
    },
}


def get_room_details(room_type):
    return ROOM_DETAILS.get(room_type, {
        "title": room_type,
        "description": "Comfortable accommodation for Nobleman's Travellers Inn guests.",
        "capacity": "Guests",
        "bed": "Bed included",
        "amenities": ["Wi-Fi", "Private bath"],
        "rules": ["Check-in: 2:00 PM", "Check-out: 12:00 PM"],
    })


def build_booking_summary(source):
    booking_summary = {
        "check_in": source.get("check_in", ""),
        "check_out": source.get("check_out", ""),
        "adults": source.get("adults", "1"),
        "children": source.get("children", "0"),
        "room_type": source.get("room_type", ""),
        "max_price": source.get("max_price", ""),
        "sort_by": source.get("sort_by", "lowest_price"),
    }
    booking_summary["guest_text"] = (
        f"{booking_summary['adults']} adult{'s' if booking_summary['adults'] != '1' else ''}, "
        f"{booking_summary['children']} child{'ren' if booking_summary['children'] != '1' else ''}"
    )
    return booking_summary


def build_guest_details(source):
    return {
        "first_name": source.get("first_name", ""),
        "last_name": source.get("last_name", ""),
        "email": source.get("email", ""),
        "phone": source.get("phone", ""),
        "requests": source.get("requests", ""),
    }


def build_price_breakdown(room):
    nights = 2
    room_total = room.price * nights
    tax_total = room_total * 0.15
    total = room_total + tax_total
    return {
        "nights": nights,
        "room_total": room_total,
        "tax_total": tax_total,
        "total": total,
    }


def build_temp_booking_id(room):
    return f"TEMP-{2000 + room.id}"


def build_booking_reference(room):
    return f"NIS-2026-{4000 + room.id}"


def render_payment_result(room_id, status):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)
    booking_summary = build_booking_summary(request.form or request.args)
    guest_details = build_guest_details(request.form or request.args)

    return render_template(
        "rooms/payment_result.html",
        room=room,
        details=details,
        booking_summary=booking_summary,
        guest_details=guest_details,
        price_breakdown=build_price_breakdown(room),
        temp_booking_id=request.values.get("temp_booking_id", build_temp_booking_id(room)),
        payment_status=status,
    )

@main.route("/")
def home():
    rooms = []
    for room_type in ["Single Room", "Double Room", "Family Room"]:
        room = (
            Room.query
            .filter_by(room_type=room_type, status="Available")
            .order_by(Room.price.asc(), Room.room_number.asc())
            .first()
        )
        if room:
            rooms.append(room)

    return render_template("index.html", rooms=rooms)

@main.route("/available-rooms")
def available_rooms():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")
    room_type = request.args.get("room_type", "")
    max_price = request.args.get("max_price", "")
    sort_by = request.args.get("sort_by", "lowest_price")

    room_types = ["Single Room", "Double Room", "Family Room"]
    rooms_query = Room.query.filter_by(status="Available")
    count_query = (
        Room.query
        .with_entities(Room.room_type, func.count(Room.id))
        .filter_by(status="Available")
    )

    if room_type:
        rooms_query = rooms_query.filter_by(room_type=room_type)
        count_query = count_query.filter_by(room_type=room_type)

    if max_price:
        try:
            max_price_value = float(max_price)
            rooms_query = rooms_query.filter(Room.price <= max_price_value)
            count_query = count_query.filter(Room.price <= max_price_value)
        except ValueError:
            max_price = ""

    if sort_by == "highest_price":
        rooms_query = rooms_query.order_by(Room.price.desc(), Room.room_number.asc())
    elif sort_by == "room_type":
        rooms_query = rooms_query.order_by(Room.room_type.asc(), Room.room_number.asc())
    else:
        rooms_query = rooms_query.order_by(Room.price.asc(), Room.room_number.asc())

    rooms = rooms_query.all()
    available_counts = {
        room_type_name: count
        for room_type_name, count in count_query.group_by(Room.room_type).all()
    }

    grouped_rooms = []
    seen_types = set()
    for room in rooms:
        if room.room_type not in seen_types:
            room.available_count = available_counts.get(room.room_type, 0)
            room.details = get_room_details(room.room_type)
            grouped_rooms.append(room)
            seen_types.add(room.room_type)

    search_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children,
        "guest_text": f"{adults} adult{'s' if adults != '1' else ''}, {children} child{'ren' if children != '1' else ''}",
        "room_type": room_type or "Any room",
        "max_price": max_price or "350",
        "sort_by": sort_by,
    }

    return render_template(
        "rooms/available_rooms.html",
        rooms=grouped_rooms,
        search_summary=search_summary,
        room_types=room_types,
    )

@main.route("/rooms/<int:room_id>")
def room_details(room_id):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)

    booking_summary = {
        "check_in": request.args.get("check_in", ""),
        "check_out": request.args.get("check_out", ""),
        "adults": request.args.get("adults", "1"),
        "children": request.args.get("children", "0"),
        "room_type": request.args.get("room_type", ""),
        "max_price": request.args.get("max_price", ""),
        "sort_by": request.args.get("sort_by", "lowest_price"),
    }
    booking_summary["guest_text"] = (
        f"{booking_summary['adults']} adult{'s' if booking_summary['adults'] != '1' else ''}, "
        f"{booking_summary['children']} child{'ren' if booking_summary['children'] != '1' else ''}"
    )

    return render_template(
        "rooms/room_details.html",
        room=room,
        details=details,
        booking_summary=booking_summary,
    )

@main.route("/rooms/<int:room_id>/book")
def booking_form(room_id):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)

    booking_summary = build_booking_summary(request.args)

    return render_template(
        "rooms/booking_form.html",
        room=room,
        details=details,
        booking_summary=booking_summary,
    )

@main.route("/rooms/<int:room_id>/review", methods=["POST"])
def booking_review(room_id):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)
    booking_summary = build_booking_summary(request.form)
    guest_details = build_guest_details(request.form)

    return render_template(
        "rooms/booking_review.html",
        room=room,
        details=details,
        booking_summary=booking_summary,
        guest_details=guest_details,
        price_breakdown=build_price_breakdown(room),
    )

@main.route("/rooms/<int:room_id>/hold", methods=["POST"])
def temporary_booking_hold(room_id):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)
    booking_summary = build_booking_summary(request.form)
    guest_details = build_guest_details(request.form)
    hold_created = room.status == "Available"

    if hold_created:
        room.status = "On Hold"
        db.session.commit()

    return render_template(
        "rooms/payment.html",
        room=room,
        details=details,
        booking_summary=booking_summary,
        guest_details=guest_details,
        price_breakdown=build_price_breakdown(room),
        temp_booking_id=build_temp_booking_id(room),
        hold_created=hold_created,
    )

@main.route("/rooms/<int:room_id>/payment/success", methods=["POST"])
def payment_success(room_id):
    room = Room.query.get_or_404(room_id)
    room.status = "Booked"
    db.session.commit()
    booking_summary = build_booking_summary(request.form)
    guest_details = build_guest_details(request.form)

    return render_template(
        "rooms/booking_confirmation.html",
        room=room,
        details=get_room_details(room.room_type),
        booking_summary=booking_summary,
        guest_details=guest_details,
        price_breakdown=build_price_breakdown(room),
        booking_reference=build_booking_reference(room),
        notification_sent=True,
    )

@main.route("/rooms/<int:room_id>/payment/notification-failed", methods=["POST"])
def payment_notification_failed(room_id):
    room = Room.query.get_or_404(room_id)
    room.status = "Booked"
    db.session.commit()
    booking_summary = build_booking_summary(request.form)
    guest_details = build_guest_details(request.form)

    return render_template(
        "rooms/booking_confirmation.html",
        room=room,
        details=get_room_details(room.room_type),
        booking_summary=booking_summary,
        guest_details=guest_details,
        price_breakdown=build_price_breakdown(room),
        booking_reference=build_booking_reference(room),
        notification_sent=False,
    )

@main.route("/rooms/<int:room_id>/payment/failed", methods=["POST"])
def payment_failed(room_id):
    return render_payment_result(room_id, "failed")

@main.route("/rooms/<int:room_id>/payment/pending", methods=["POST"])
def payment_pending(room_id):
    return render_payment_result(room_id, "pending")

@main.route("/rooms/<int:room_id>/check-availability")
def check_room_availability(room_id):
    room = Room.query.get_or_404(room_id)
    details = get_room_details(room.room_type)

    return render_template(
        "rooms/check_availability.html",
        room=room,
        details=details,
        booking_summary={
            "check_in": request.args.get("check_in", ""),
            "check_out": request.args.get("check_out", ""),
            "adults": request.args.get("adults", "1"),
            "children": request.args.get("children", "0"),
        },
    )

@main.route("/login")
def login_selection():
    return render_template("login_selection.html")
