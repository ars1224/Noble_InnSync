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
            "available_count": Room.query.filter_by(
                room_type="Single Room",
                status="Available"
            ).count(),
            "image": "room1.jpg"
        },

        {
            "room_type": "Double Room",
            "description": "Ideal for couples with spacious comfort and modern amenities.",
            "price": 229,
            "available_count": Room.query.filter_by(
                room_type="Double Room",
                status="Available"
            ).count(),
            "image": "room2.jpg"
        },

        {
            "room_type": "Family Room",
            "description": "Designed for families and groups with extra space and comfort.",
            "price": 329,
            "available_count": Room.query.filter_by(
                room_type="Family Room",
                status="Available"
            ).count(),
            "image": "room3.jpg"
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