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
        "adult_capacity": 4,
        "child_capacity": 2,
        "price": 329
    },
    "Double Room": {
        "adult_capacity": 2,
        "child_capacity": 1,
        "price": 229
    },
    "Single Room": {
        "adult_capacity": 1,
        "child_capacity": 0,
        "price": 149
    }
}


def suggest_rooms(adults, children):
    selected_rooms = []

    remaining_adults = adults
    remaining_children = children

    room_priority = ["Family Room", "Double Room", "Single Room"]

    for room_type in room_priority:
        rule = ROOM_RULES[room_type]

        available_rooms = Room.query.filter_by(
            room_type=room_type,
            status="Available"
        ).all()

        for room in available_rooms:

            if remaining_adults <= 0 and remaining_children <= 0:
                break

            # Skip Single Room if only children are left
            if room_type == "Single Room" and remaining_adults <= 0:
                continue

            selected_rooms.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price": rule["price"],
                "adult_capacity": rule["adult_capacity"],
                "child_capacity": rule["child_capacity"]
            })

            remaining_adults -= rule["adult_capacity"]
            remaining_children -= rule["child_capacity"]

            if remaining_adults < 0:
                remaining_adults = 0

            if remaining_children < 0:
                remaining_children = 0

    total_adult_capacity = sum(room["adult_capacity"] for room in selected_rooms)
    total_child_capacity = sum(room["child_capacity"] for room in selected_rooms)
    total_price = sum(room["price"] for room in selected_rooms)

    return {
        "selected_rooms": selected_rooms,
        "total_adult_capacity": total_adult_capacity,
        "total_child_capacity": total_child_capacity,
        "total_price": total_price,
        "can_fit": total_adult_capacity >= adults and total_child_capacity >= children
    }


@booking.route("/book-room", methods=["GET", "POST"])
def book_room():

    room_images = {
        "Single Room": "ChatGPT Image Jun 2, 2026, 08_37_08 PM.png",
        "Double Room": "ChatGPT Image Jun 2, 2026, 08_37_54 PM.png",
        "Family Room": "ChatGPT Image Jun 2, 2026, 08_38_19 PM.png",
    }

    if request.method == "POST":

        adults = int(request.form.get("adults", 1))
        children = int(request.form.get("children", 0))

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
                adult_capacity=selected["adult_capacity"],
                child_capacity=selected["child_capacity"]
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
    "bookings/booking_form.html"
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
        "total_adult_capacity": room_plan["total_adult_capacity"],
        "total_child_capacity": room_plan["total_child_capacity"],
        "total_price": room_plan["total_price"]
    }