from flask import Blueprint, render_template, request
from app.models.room import Room

main = Blueprint("main", __name__)

@main.route("/")
def home():
    rooms = Room.query.all()
    return render_template("index.html", rooms=rooms)

@main.route("/available-rooms")
def available_rooms():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    adults = request.args.get("adults", "1")
    children = request.args.get("children", "0")

    rooms = Room.query.filter_by(status="Available").order_by(Room.price.asc()).all()

    search_summary = {
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children,
        "guest_text": f"{adults} adult{'s' if adults != '1' else ''}, {children} child{'ren' if children != '1' else ''}",
    }

    return render_template("available_rooms.html", rooms=rooms, search_summary=search_summary)

@main.route("/login")
def login_selection():
    return render_template("login_selection.html")
