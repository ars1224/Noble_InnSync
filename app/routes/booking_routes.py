from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.accounting import Accounting
from app.models.room import Room
from app.utils.pricing import calculate_stay_total
import random

booking = Blueprint("booking", __name__)

TAX_RATE = 0.15


def generate_reference_number():
    return "NIS" + str(random.randint(100000, 999999))


def generate_transaction_number():
    return "TXN" + str(random.randint(100000, 999999))


def add_tax_and_fees(room_total):
    tax_total = round(float(room_total) * TAX_RATE, 2)
    return tax_total, round(float(room_total) + tax_total, 2)


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


def available_rooms_for_type(room_type, check_in="", check_out=""):
    rooms = (
        Room.query
        .filter(Room.room_type == room_type, Room.status != "Maintenance")
        .order_by(Room.room_number.asc())
        .all()
    )

    if check_in and check_out:
        booked_room_numbers = booked_room_numbers_for_dates(check_in, check_out)
        return [
            room for room in rooms
            if room.room_number not in booked_room_numbers
        ]

    return [
        room for room in rooms
        if room.status == "Available"
    ]


def suggest_rooms(adults, children, check_in="", check_out=""):
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

        available_rooms = available_rooms_for_type(room_type, check_in, check_out)

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
    nightly_total = sum(room["price"] for room in selected_rooms)

    return {
        "selected_rooms": selected_rooms,
        "required_capacity": required_capacity,
        "total_capacity": total_capacity,
        "nightly_total": nightly_total,
        "can_fit": total_capacity >= required_capacity
    }

def build_manual_room_plan(room_ids, adults, children, check_in="", check_out=""):
    selected_rooms = []
    required_capacity = calculate_required_capacity(adults, children)

    rooms = Room.query.filter(Room.id.in_(room_ids), Room.status != "Maintenance").all()
    booked_room_numbers = booked_room_numbers_for_dates(check_in, check_out)

    for room in rooms:
        if check_in and check_out and room.room_number in booked_room_numbers:
            continue

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
    nightly_total = sum(room["price"] for room in selected_rooms)

    return {
        "selected_rooms": selected_rooms,
        "required_capacity": required_capacity,
        "total_capacity": total_capacity,
        "nightly_total": nightly_total,
        "can_fit": total_capacity >= required_capacity
    }

@booking.route("/book-room", methods=["GET", "POST"])
def book_room():

    if request.method == "POST":

        adults = int(request.form.get("adults", 1))
        children = int(request.form.get("children", 0))
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        payment_method = request.form.get("payment_method", "Pay on Arrival")
        normalized_payment_method = (
            "Card" if payment_method == "Card Payment" else "Pay on Arrival"
        )
        payment_status = (
            "Paid" if normalized_payment_method == "Card" else "Unpaid"
        )

        selected_room_ids = request.form.get("selected_room_ids", "").strip()

        if selected_room_ids:
            room_ids = [int(room_id) for room_id in selected_room_ids.split(",") if room_id]
            room_plan = build_manual_room_plan(room_ids, adults, children, check_in, check_out)
        else:
            room_plan = suggest_rooms(adults, children, check_in, check_out)

        if not room_plan["can_fit"]:
            return "Not enough available room capacity for this booking."

        try:
            nights, room_total = calculate_stay_total(
                room_plan["nightly_total"],
                check_in,
                check_out
            )
            tax_total, total_price = add_tax_and_fees(room_total)
        except ValueError as error:
            return str(error), 400

        new_booking = Booking(
            guest_name=request.form.get("guest_name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            total_price=total_price,
            status="Confirmed" if payment_status == "Paid" else "Pending",
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
            room_record.status = "Reserved"

        accounting_record = Accounting(
            transaction_no=generate_transaction_number(),
            booking_id=new_booking.id,
            check_in=new_booking.check_in,
            check_out=new_booking.check_out,
            total_price=total_price,
            payment_status=payment_status,
            payment_method=normalized_payment_method
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
        children=request.args.get("children", 0),
        check_in=request.args.get("check_in", ""),
        check_out=request.args.get("check_out", "")
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
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")

    room_plan = suggest_rooms(adults, children, check_in, check_out)

    response = {
        "can_fit": room_plan["can_fit"],
        "selected_rooms": room_plan["selected_rooms"],
        "required_capacity": room_plan["required_capacity"],
        "total_capacity": room_plan["total_capacity"],
        "nightly_total": room_plan["nightly_total"],
        "tax_total": 0,
        "nights": None,
        "total_price": room_plan["nightly_total"]
    }

    if check_in and check_out:
        try:
            nights, room_total = calculate_stay_total(
                room_plan["nightly_total"],
                check_in,
                check_out
            )
            tax_total, total_price = add_tax_and_fees(room_total)
            response["nights"] = nights
            response["room_total"] = room_total
            response["tax_total"] = tax_total
            response["total_price"] = total_price
        except ValueError as error:
            response["date_error"] = str(error)

    return response

@booking.route("/available-room-options")
def available_room_options():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    booked_room_numbers = booked_room_numbers_for_dates(check_in, check_out)

    rooms = Room.query.filter(Room.status != "Maintenance").all()

    room_options = []

    for room in rooms:
        if check_in and check_out and room.room_number in booked_room_numbers:
            continue

        if not check_in and not check_out and room.status != "Available":
            continue

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
