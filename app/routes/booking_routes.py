from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.accounting import Accounting
from app.models.room import Room
import random

booking = Blueprint("booking", __name__)


def generate_reference_number():
    return "NIS" + str(random.randint(100000, 999999))


def generate_transaction_number():
    return "TXN" + str(random.randint(100000, 999999))


ROOM_RULES = {
    "Family Room": {
        "capacity": 6,
        "price": 329
    },
    "Double Room": {
        "capacity": 3,
        "price": 229
    },
    "Single Room": {
        "capacity": 1,
        "price": 149
    }
}


def calculate_required_capacity(adults, children):
    return adults + (children * 0.5)


def suggest_rooms(adults, children):
    selected_rooms = []

    required_capacity = calculate_required_capacity(adults, children)
    remaining_capacity = required_capacity

    if required_capacity <= 1:
        room_priority = ["Single Room", "Double Room", "Family Room"]
    elif required_capacity <= 3:
        room_priority = ["Double Room", "Family Room", "Single Room"]
    else:
        room_priority = ["Family Room", "Double Room", "Single Room"]

    for room_type in room_priority:
        rule = ROOM_RULES[room_type]

        available_rooms = Room.query.filter_by(
            room_type=room_type,
            status="Available"
        ).all()

        for room in available_rooms:
            if remaining_capacity <= 0:
                break

            selected_rooms.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price": rule["price"],
                "capacity": rule["capacity"]
            })

            remaining_capacity -= rule["capacity"]

    total_capacity = sum(room["capacity"] for room in selected_rooms)
    total_price = sum(room["price"] for room in selected_rooms)

    return {
        "selected_rooms": selected_rooms,
        "required_capacity": required_capacity,
        "total_capacity": total_capacity,
        "total_price": total_price,
        "can_fit": total_capacity >= required_capacity
    }

def build_manual_room_plan(room_ids, adults, children):
    selected_rooms = []
    required_capacity = calculate_required_capacity(adults, children)

    rooms = Room.query.filter(Room.id.in_(room_ids), Room.status == "Available").all()

    for room in rooms:
        rule = ROOM_RULES.get(room.room_type)

        if rule:
            selected_rooms.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price": rule["price"],
                "capacity": rule["capacity"]
            })

    total_capacity = sum(room["capacity"] for room in selected_rooms)
    total_price = sum(room["price"] for room in selected_rooms)

    return {
        "selected_rooms": selected_rooms,
        "required_capacity": required_capacity,
        "total_capacity": total_capacity,
        "total_price": total_price,
        "can_fit": total_capacity >= required_capacity
    }

@booking.route("/book-room", methods=["GET", "POST"])
def book_room():

    if request.method == "POST":

        adults = int(request.form.get("adults", 1))
        children = int(request.form.get("children", 0))

        selected_room_ids = request.form.get("selected_room_ids", "").strip()

        if selected_room_ids:
            room_ids = [int(room_id) for room_id in selected_room_ids.split(",") if room_id]
            room_plan = build_manual_room_plan(room_ids, adults, children)
        else:
            room_plan = suggest_rooms(adults, children)

        if not room_plan["can_fit"]:
            return "Not enough available room capacity for this booking."

        new_booking = Booking(
            guest_name=request.form.get("guest_name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            check_in=request.form.get("check_in"),
            check_out=request.form.get("check_out"),
            adults=adults,
            children=children,
            total_price=room_plan["total_price"],
            reference_number=generate_reference_number()
        )

        db.session.add(new_booking)
        db.session.flush()

        for selected in room_plan["selected_rooms"]:

            booking_room = BookingRoom(
                booking_id=new_booking.id,
                room_number=selected["room_number"],
                room_type=selected["room_type"],
                price=selected["price"],
                adult_capacity=selected["capacity"],
                child_capacity=0
            )

            db.session.add(booking_room)

            room_record = Room.query.get(selected["room_id"])
            room_record.status = "Booked"

        accounting_record = Accounting(
            transaction_no=generate_transaction_number(),
            booking_id=new_booking.id,
            check_in=new_booking.check_in,
            check_out=new_booking.check_out,
            total_price=room_plan["total_price"],
            payment_status="Unpaid",
            payment_method="Pay on Arrival"
        )

        db.session.add(accounting_record)
        db.session.commit()

        return redirect(
            url_for(
                "booking.booking_success",
                reference_number=new_booking.reference_number
            )
        )

    return render_template(
        "bookings/booking_form.html",
        adults=request.args.get("adults", 1),
        children=request.args.get("children", 0)
    )


@booking.route("/booking-success/<reference_number>")
def booking_success(reference_number):

    booking_record = Booking.query.filter_by(
        reference_number=reference_number
    ).first_or_404()

    return render_template(
        "bookings/booking_success.html",
        booking=booking_record
    )


@booking.route("/suggest-rooms")
def suggest_rooms_api():
    adults = int(request.args.get("adults", 1))
    children = int(request.args.get("children", 0))

    room_plan = suggest_rooms(adults, children)

    return {
        "can_fit": room_plan["can_fit"],
        "selected_rooms": room_plan["selected_rooms"],
        "required_capacity": room_plan["required_capacity"],
        "total_capacity": room_plan["total_capacity"],
        "total_price": room_plan["total_price"]
    }

@booking.route("/available-room-options")
def available_room_options():
    rooms = Room.query.filter_by(status="Available").all()

    room_options = []

    for room in rooms:
        rule = ROOM_RULES.get(room.room_type)

        if rule:
            room_options.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price": rule["price"],
                "capacity": rule["capacity"]
            })

    return {
        "rooms": room_options
    }