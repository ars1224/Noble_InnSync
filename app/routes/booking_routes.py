import re
from datetime import date
from decimal import Decimal

from flask import Blueprint, abort, render_template, request, redirect, url_for
from app import db
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.accounting import Accounting
from app.models.room import Room
from app.utils.pricing import calculate_stay_total
from app.utils.reservations import (
    authorize_reservation,
    begin_booking_transaction,
    booked_room_numbers_for_dates,
    generate_reference_number,
    generate_transaction_number,
    reservation_is_authorized,
)

booking = Blueprint("booking", __name__)

TAX_RATE = 0.15
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)
EXPIRY_PATTERN = re.compile(r"^\d{2}/\d{2}$")
PAYMENT_METHODS = {"Pay on Arrival", "Card Payment"}


def add_tax_and_fees(room_total):
    room_total = Decimal(str(room_total))
    tax_total = (room_total * Decimal(str(TAX_RATE))).quantize(Decimal("0.01"))
    return tax_total, (room_total + tax_total).quantize(Decimal("0.01"))


def booking_form_values(source=None):
    source = source or {}
    return {
        "guest_name": source.get("guest_name", "").strip(),
        "email": source.get("email", "").strip(),
        "phone": source.get("phone", "").strip(),
        "check_in": source.get("check_in", "").strip(),
        "check_out": source.get("check_out", "").strip(),
        "adults": source.get("adults", "1") or "1",
        "children": source.get("children", "0") or "0",
        "selected_room_ids": source.get("selected_room_ids", "").strip(),
        "payment_method": source.get("payment_method", "Pay on Arrival"),
        "cardholder_name": source.get("cardholder_name", "").strip(),
        "card_number": source.get("card_number", "").strip(),
        "expiry": source.get("expiry", "").strip(),
        "cvv": source.get("cvv", "").strip(),
    }


def render_booking_form(form_values=None, form_errors=None, status_code=200):
    form_values = form_values or booking_form_values(request.args)
    rendered_page = render_template(
        "bookings/booking_form.html",
        form_values=form_values,
        form_errors=form_errors or [],
        adults=form_values["adults"],
        children=form_values["children"],
        check_in=form_values["check_in"],
        check_out=form_values["check_out"],
    )
    return rendered_page, status_code


def validate_booking_form(form_values, today=None):
    today = today or date.today()
    errors = []

    if not form_values["guest_name"]:
        errors.append("Full name is required.")

    if not EMAIL_PATTERN.fullmatch(form_values["email"]):
        errors.append("Enter a valid email address, for example name@example.com.")

    phone = form_values["phone"]
    if not phone:
        errors.append("Phone number is required.")
    elif re.search(r"[^0-9\s]", phone):
        errors.append("Phone number can contain digits and spaces only.")
    else:
        phone_digits = phone.replace(" ", "")
        if not 9 <= len(phone_digits) <= 11:
            errors.append("Phone number must contain 9 to 11 digits.")

    if form_values["payment_method"] not in PAYMENT_METHODS:
        errors.append("Choose a valid payment method.")

    if form_values["payment_method"] == "Card Payment":
        if not form_values["cardholder_name"]:
            errors.append("Cardholder name is required.")

        card_number = form_values["card_number"]
        if re.search(r"[^0-9\s]", card_number):
            errors.append("Card number can contain digits and spaces only.")
        elif len(card_number.replace(" ", "")) != 16:
            errors.append("Card number must contain exactly 16 digits.")

        expiry = form_values["expiry"]
        if not EXPIRY_PATTERN.fullmatch(expiry):
            errors.append("Expiry date must use MM/YY format.")
        else:
            expiry_month = int(expiry[:2])
            expiry_year = 2000 + int(expiry[-2:])

            if not 1 <= expiry_month <= 12:
                errors.append("Expiry month must be between 01 and 12.")
            elif (
                expiry_year < today.year
                or (expiry_year == today.year and expiry_month < today.month)
            ):
                errors.append("Expiry date must not be expired.")

        if not re.fullmatch(r"\d{3}", form_values["cvv"]):
            errors.append("CVV must contain exactly 3 digits.")

    return errors


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
        form_values = booking_form_values(request.form)
        form_errors = validate_booking_form(form_values)

        try:
            adults = int(form_values["adults"])
            children = int(form_values["children"])
        except (TypeError, ValueError):
            adults = None
            children = None
            form_errors.append("Guest counts must be valid numbers.")

        if adults is not None and adults < 1:
            form_errors.append("Adults must be at least 1.")

        if children is not None and children < 0:
            form_errors.append("Children cannot be negative.")

        if form_errors:
            return render_booking_form(form_values, form_errors, 400)

        check_in = form_values["check_in"]
        check_out = form_values["check_out"]
        payment_method = form_values["payment_method"]
        normalized_payment_method = (
            "Card" if payment_method == "Card Payment" else "Pay on Arrival"
        )
        payment_status = (
            "Paid" if normalized_payment_method == "Card" else "Unpaid"
        )

        selected_room_ids = form_values["selected_room_ids"]
        if selected_room_ids:
            try:
                room_ids = [
                    int(room_id)
                    for room_id in selected_room_ids.split(",")
                    if room_id
                ]
            except ValueError:
                return render_booking_form(
                    form_values,
                    ["Choose valid rooms for this booking."],
                    400,
                )
        else:
            room_ids = []

        begin_booking_transaction()

        if selected_room_ids:
            room_plan = build_manual_room_plan(room_ids, adults, children, check_in, check_out)
        else:
            room_plan = suggest_rooms(adults, children, check_in, check_out)

        if not room_plan["can_fit"]:
            db.session.rollback()
            return render_booking_form(
                form_values,
                ["Not enough available room capacity for this booking."],
                400,
            )

        try:
            nights, room_total = calculate_stay_total(
                room_plan["nightly_total"],
                check_in,
                check_out
            )
            tax_total, total_price = add_tax_and_fees(room_total)
        except ValueError as error:
            db.session.rollback()
            return render_booking_form(form_values, [str(error)], 400)

        new_booking = Booking(
            guest_name=form_values["guest_name"],
            email=form_values["email"],
            phone=form_values["phone"],
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

            room_record = db.session.get(Room, selected["room_id"])
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
        authorize_reservation(new_booking.reference_number)

        return redirect(
            url_for(
                "booking.booking_success",
                reference_number=new_booking.reference_number
            )
        )

    return render_booking_form()


@booking.route("/booking-success/<reference_number>")
def booking_success(reference_number):

    if not reservation_is_authorized(reference_number):
        abort(404)

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
            response["room_total"] = float(room_total)
            response["tax_total"] = float(tax_total)
            response["total_price"] = float(total_price)
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
