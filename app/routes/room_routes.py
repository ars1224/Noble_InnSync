from flask import Blueprint, abort, render_template, request

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


@room.route("/available-rooms")
def available_rooms():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

    room_summary = [
        build_room_summary(room_slug, details)
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
