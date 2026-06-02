from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.booking import Booking
import random

booking = Blueprint("booking", __name__)

def generate_reference_number():
    return "NIS" + str(random.randint(100000, 999999))


@booking.route("/book-room", methods=["GET", "POST"])
def book_room():

    if request.method == "POST":
        new_booking = Booking(
            guest_name=request.form.get("guest_name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            room_type=request.form.get("room_type"),
            check_in=request.form.get("check_in"),
            check_out=request.form.get("check_out"),
            adults=request.form.get("adults"),
            children=request.form.get("children"),
            reference_number=generate_reference_number()
        )

        db.session.add(new_booking)
        db.session.commit()

        return redirect(
            url_for(
                "booking.booking_success",
                reference_number=new_booking.reference_number
            )
        )

    return render_template("bookings/booking_form.html")


@booking.route("/booking-success/<reference_number>")
def booking_success(reference_number):

    booking_record = Booking.query.filter_by(
        reference_number=reference_number
    ).first_or_404()

    return render_template(
        "bookings/booking_success.html",
        booking=booking_record
    )