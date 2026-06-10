from flask import Blueprint, render_template, request
from app.models.room import Room

room = Blueprint("room", __name__)

@room.route("/available-rooms")
def available_rooms():

    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

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

    search_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children,
        "guest_text":
            f"{adults} adult{'s' if adults != '1' else ''}, "
            f"{children} child{'ren' if children != '1' else ''}",
    }

    return render_template(
        "rooms/available_rooms.html",
        room_summary=room_summary,
        search_summary=search_summary
    )