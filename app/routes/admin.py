from flask import Blueprint, render_template, redirect, url_for, request, session

from app import db
from app.models.booking import Booking
from app.models.room import Room
from app.models.accounting import Accounting
from app.utils.auth import login_required, role_required
from datetime import datetime
from app.models.booking_room import BookingRoom
from app.models.inventory import InventoryItem
from app.models.equipment import EquipmentIssue
from app.models.activity_log import ActivityLog


admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/dashboard")
@login_required
def dashboard():
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status="Pending").count()
    confirmed_bookings = Booking.query.filter_by(status="Confirmed").count()
    available_rooms = Room.query.filter_by(status="Available").count()

    paid_transactions = Accounting.query.filter_by(payment_status="Paid").all()
    total_revenue = sum(transaction.total_price for transaction in paid_transactions)

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    low_stock_count = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.reorder_level
    ).count()
    equipment_issue_count = EquipmentIssue.query.filter(
        EquipmentIssue.status != "Working"
    ).count()
    pending_alert_count = ActivityLog.query.filter(
        ActivityLog.delivery_status.in_(["Pending", "Failed"])
    ).count()

    return render_template(
        "admin/dashboard.html",
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        available_rooms=available_rooms,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        low_stock_count=low_stock_count,
        equipment_issue_count=equipment_issue_count,
        pending_alert_count=pending_alert_count
    )


def add_activity(event_type, message, delivery_status="Pending"):
    activity = ActivityLog(
        event_type=event_type,
        message=message,
        delivery_status=delivery_status,
        created_by=session.get("username", "system"),
        target_role="manager",
    )
    db.session.add(activity)


@admin.route("/inventory")
@login_required
@role_required(["admin", "staff", "manager"])
def inventory():
    items = InventoryItem.query.order_by(InventoryItem.item_name.asc()).all()
    low_stock_count = sum(item.stock_status != "OK" for item in items)
    alerts_sent = ActivityLog.query.filter_by(
        event_type="Inventory", delivery_status="Sent"
    ).count()

    return render_template(
        "admin/inventory.html",
        items=items,
        low_stock_count=low_stock_count,
        alerts_sent=alerts_sent,
    )


@admin.route("/inventory/add", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def add_inventory_item():
    item_name = request.form.get("item_name", "").strip()
    if item_name and not InventoryItem.query.filter_by(item_name=item_name).first():
        item = InventoryItem(
            item_name=item_name,
            category=request.form.get("category", "Guest Supplies").strip(),
            current_stock=max(0, request.form.get("current_stock", 0, type=int)),
            reorder_level=max(0, request.form.get("reorder_level", 10, type=int)),
            unit=request.form.get("unit", "items").strip(),
        )
        db.session.add(item)
        add_activity("Inventory", f"{item_name} was added to inventory.", "Sent")
        db.session.commit()

    return redirect(url_for("admin.inventory"))


@admin.route("/inventory/<int:item_id>/update", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    item.current_stock = max(
        0, request.form.get("current_stock", item.current_stock, type=int)
    )
    item.reorder_level = max(
        0, request.form.get("reorder_level", item.reorder_level, type=int)
    )
    add_activity(
        "Inventory",
        f"{item.item_name} stock updated to {item.current_stock} {item.unit}.",
        "Sent",
    )
    db.session.commit()
    return redirect(url_for("admin.inventory"))


@admin.route("/inventory/<int:item_id>/add-stock", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def add_inventory_stock(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    quantity = max(0, request.form.get("quantity", 0, type=int))
    item.current_stock += quantity
    add_activity(
        "Inventory",
        f"Added {quantity} {item.unit} to {item.item_name}.",
        "Sent",
    )
    db.session.commit()
    return redirect(url_for("admin.inventory"))


@admin.route("/inventory/<int:item_id>/send-alert", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def send_inventory_alert(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    add_activity(
        "Inventory",
        f"Low-stock alert: {item.item_name} has {item.current_stock} {item.unit} remaining.",
        "Sent",
    )
    db.session.commit()
    return redirect(url_for("admin.inventory"))


@admin.route("/equipment")
@login_required
@role_required(["admin", "staff", "manager"])
def equipment():
    issues = EquipmentIssue.query.order_by(EquipmentIssue.created_at.desc()).all()
    rooms = Room.query.order_by(Room.room_number.asc()).all()
    return render_template("admin/equipment.html", issues=issues, rooms=rooms)


@admin.route("/equipment/report", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def report_equipment_issue():
    room = Room.query.get_or_404(request.form.get("room_id", type=int))
    equipment_name = request.form.get("equipment_name", "").strip()
    if equipment_name:
        issue = EquipmentIssue(
            room_id=room.id,
            equipment_name=equipment_name,
            status=request.form.get("status", "Check Needed"),
            priority=request.form.get("priority", "Medium"),
            notes=request.form.get("notes", "").strip(),
            reported_by=session.get("username", "staff"),
        )
        db.session.add(issue)
        add_activity(
            "Equipment",
            f"{equipment_name} issue reported for room {room.room_number}.",
        )
        db.session.commit()

    return redirect(url_for("admin.equipment"))


@admin.route("/equipment/<int:issue_id>/request-maintenance", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def request_equipment_maintenance(issue_id):
    issue = EquipmentIssue.query.get_or_404(issue_id)
    issue.maintenance_status = "Requested"
    if issue.status == "Broken":
        issue.room.status = "Maintenance"
    add_activity(
        "Equipment",
        f"Maintenance requested for {issue.equipment_name} in room {issue.room.room_number}.",
    )
    db.session.commit()
    return redirect(url_for("admin.equipment"))


@admin.route("/equipment/<int:issue_id>/resolve", methods=["POST"])
@login_required
@role_required(["admin", "manager"])
def resolve_equipment_issue(issue_id):
    issue = EquipmentIssue.query.get_or_404(issue_id)
    issue.status = "Working"
    issue.maintenance_status = "Resolved"
    if issue.room.status == "Maintenance":
        issue.room.status = "Available"
    add_activity(
        "Equipment",
        f"{issue.equipment_name} in room {issue.room.room_number} marked resolved.",
        "Sent",
    )
    db.session.commit()
    return redirect(url_for("admin.equipment"))


@admin.route("/activity-log")
@login_required
@role_required(["admin", "staff", "manager"])
def activity_log():
    activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    return render_template("admin/activity_log.html", activities=activities)


@admin.route("/activity-log/<int:activity_id>/resend", methods=["POST"])
@login_required
@role_required(["admin", "manager"])
def resend_activity(activity_id):
    activity = ActivityLog.query.get_or_404(activity_id)
    activity.delivery_status = "Sent"
    db.session.commit()
    return redirect(url_for("admin.activity_log"))


@admin.route("/bookings")
@login_required
@role_required(["admin", "staff"])
def bookings():
    search = request.args.get("search", "").strip()

    query = Booking.query

    if search:
        query = query.filter(
            db.or_(
                Booking.reference_number.ilike(f"%{search}%"),
                Booking.guest_name.ilike(f"%{search}%"),
                Booking.email.ilike(f"%{search}%"),
                Booking.phone.ilike(f"%{search}%"),
                Booking.status.ilike(f"%{search}%")
            )
        )

    all_bookings = query.order_by(Booking.created_at.desc()).all()

    return render_template(
        "admin/bookings.html",
        bookings=all_bookings,
        search=search
    )


@admin.route("/rooms")
@login_required
@role_required(["admin", "staff"])
def rooms():
    all_rooms = Room.query.order_by(Room.room_number.asc()).all()

    return render_template(
        "admin/rooms.html",
        rooms=all_rooms
    )


@admin.route("/payments")
@login_required
@role_required(["admin", "manager"])
def payments():
    all_payments = Accounting.query.order_by(Accounting.created_at.desc()).all()

    return render_template(
        "admin/payments.html",
        payments=all_payments
    )


@admin.route("/reports")
@login_required
@role_required(["admin", "manager"])
def reports():
    total_bookings = Booking.query.count()

    paid_payments = Accounting.query.filter_by(payment_status="Paid").count()
    unpaid_payments = Accounting.query.filter_by(payment_status="Unpaid").count()

    paid_transactions = Accounting.query.filter_by(payment_status="Paid").all()
    total_revenue = sum(payment.total_price for payment in paid_transactions)

    occupied_rooms = Room.query.filter_by(status="Occupied").count()
    maintenance_rooms = Room.query.filter_by(status="Maintenance").count()

    return render_template(
        "admin/reports.html",
        total_bookings=total_bookings,
        paid_payments=paid_payments,
        unpaid_payments=unpaid_payments,
        total_revenue=total_revenue,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms
    )


@admin.route("/bookings/<int:booking_id>/approve")
@login_required
@role_required(["admin", "staff"])
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "Confirmed"

    db.session.commit()

    return redirect(url_for("admin.bookings"))


@admin.route("/bookings/<int:booking_id>/cancel")
@login_required
@role_required(["admin", "staff"])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "Cancelled"

    db.session.commit()

    return redirect(url_for("admin.bookings"))


@admin.route("/rooms/<int:room_id>/update-status", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def update_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    new_status = request.form.get("status")

    if new_status in ["Available", "Occupied", "Maintenance"]:
        room.status = new_status
        db.session.commit()

    return redirect(url_for("admin.rooms"))


@admin.route("/payments/<int:payment_id>/update-status", methods=["POST"])
@login_required
@role_required(["admin", "manager"])
def update_payment_status(payment_id):
    payment = Accounting.query.get_or_404(payment_id)

    new_status = request.form.get("payment_status")
    new_method = request.form.get("payment_method")

    allowed_statuses = ["Unpaid", "Paid", "Refunded"]
    allowed_methods = ["Pay on Arrival", "Card"]

    if new_status in allowed_statuses:
        payment.payment_status = new_status

    if new_method in allowed_methods:
        payment.payment_method = new_method

    db.session.commit()

    return redirect(url_for("admin.payments"))

@admin.route("/access-denied")
@login_required
def access_denied():
    return render_template("admin/access_denied.html")

@admin.route("/rooms/add", methods=["GET", "POST"])
@login_required
@role_required(["admin"])
def add_room():
    if request.method == "POST":
        room = Room(
            room_number=request.form.get("room_number"),
            room_type=request.form.get("room_type"),
            description=request.form.get("description"),
            price=float(request.form.get("price")),
            status=request.form.get("status")
        )

        db.session.add(room)
        db.session.commit()

        return redirect(url_for("admin.rooms"))

    return render_template("admin/add_room.html")


@admin.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["admin"])
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)

    if request.method == "POST":
        room.room_number = request.form.get("room_number")
        room.room_type = request.form.get("room_type")
        room.description = request.form.get("description")
        room.price = float(request.form.get("price"))
        room.status = request.form.get("status")

        db.session.commit()

        return redirect(url_for("admin.rooms"))

    return render_template("admin/edit_room.html", room=room)


@admin.route("/rooms/<int:room_id>/delete")
@login_required
@role_required(["admin"])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)

    db.session.delete(room)
    db.session.commit()

    return redirect(url_for("admin.rooms"))

@admin.route("/bookings/<int:booking_id>")
@login_required
@role_required(["admin", "staff"])
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    return render_template(
        "admin/booking_details.html",
        booking=booking
    )

@admin.route("/bookings/<int:booking_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["admin", "staff"])
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if request.method == "POST":
        booking.guest_name = request.form.get("guest_name")
        booking.email = request.form.get("email")
        booking.phone = request.form.get("phone")
        booking.check_in = request.form.get("check_in")
        booking.check_out = request.form.get("check_out")
        booking.adults = int(request.form.get("adults"))
        booking.children = int(request.form.get("children"))
        booking.total_price = float(request.form.get("total_price"))
        booking.status = request.form.get("status")
        if booking.status == "Checked In":
            for booked_room in booking.booking_rooms:
                room = Room.query.filter_by(room_number=booked_room.room_number).first()
                if room:
                    room.status = "Occupied"

        elif booking.status in ["Checked Out", "Cancelled"]:
            for booked_room in booking.booking_rooms:
                room = Room.query.filter_by(room_number=booked_room.room_number).first()
                if room:
                    room.status = "Available"

        db.session.commit()

        return redirect(url_for("admin.booking_details", booking_id=booking.id))

    return render_template(
        "admin/edit_booking.html",
        booking=booking
    )

@admin.route("/bookings/<int:booking_id>/payment", methods=["GET", "POST"])
@login_required
@role_required(["admin", "staff", "manager"])
def booking_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    payment = Accounting.query.filter_by(booking_id=booking.id).first()

    if request.method == "POST":
        payment_status = request.form.get("payment_status")
        payment_method = request.form.get("payment_method")

        if payment:
            payment.payment_status = payment_status
            payment.payment_method = payment_method
            payment.total_price = booking.total_price
        else:
            payment = Accounting(
                transaction_no=f"TXN-{booking.reference_number}",
                booking_id=booking.id,
                check_in=booking.check_in,
                check_out=booking.check_out,
                total_price=booking.total_price,
                payment_status=payment_status,
                payment_method=payment_method
            )
            db.session.add(payment)

        db.session.commit()

        return redirect(url_for("admin.bookings"))

    return render_template(
        "admin/booking_payment.html",
        booking=booking,
        payment=payment
    )

@admin.route("/bookings/<int:booking_id>/update-status/<status>")
@login_required
@role_required(["admin", "staff"])
def update_booking_status(booking_id, status):
    booking = Booking.query.get_or_404(booking_id)

    allowed_statuses = {
        "confirmed": "Confirmed",
        "checked-in": "Checked In",
        "checked-out": "Checked Out",
        "cancelled": "Cancelled"
    }

    if status not in allowed_statuses:
        return redirect(url_for("admin.bookings"))

    booking.status = allowed_statuses[status]

    for booked_room in booking.booking_rooms:
        room = Room.query.filter_by(
            room_number=booked_room.room_number
        ).first()

        if room:
            if status == "checked-in":
                room.status = "Occupied"

            elif status in ["checked-out", "cancelled"]:
                room.status = "Available"

    db.session.commit()

    return redirect(url_for("admin.bookings"))

@admin.route("/walk-in-booking", methods=["GET", "POST"])
@login_required
@role_required(["admin", "staff"])
def walkin_booking():
    available_rooms = Room.query.order_by(Room.room_number.asc()).all()

    if request.method == "POST":
        selected_room_ids = request.form.getlist("room_ids")

        if not selected_room_ids:
            return redirect(url_for("admin.walkin_booking"))

        guest_name = request.form.get("guest_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        adults = int(request.form.get("adults"))
        children = int(request.form.get("children"))
        payment_status = request.form.get("payment_status")
        payment_method = request.form.get("payment_method")

        selected_rooms = Room.query.filter(Room.id.in_(selected_room_ids)).all()

        valid_rooms = []

        for room in selected_rooms:
            if room.status == "Available":
                valid_rooms.append(room)

        if not valid_rooms:
            return redirect(url_for("admin.walkin_booking"))

        total_price = sum(room.price for room in valid_rooms)

        reference_number = "WALK-" + datetime.now().strftime("%Y%m%d%H%M%S")
        transaction_no = "TXN-" + reference_number

        booking = Booking(
            reference_number=reference_number,
            guest_name=guest_name,
            email=email,
            phone=phone,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            total_price=total_price,
            status="Checked In"
        )

        db.session.add(booking)
        db.session.flush()

        for room in valid_rooms:
            booking_room = BookingRoom(
                booking_id=booking.id,
                room_number=room.room_number,
                room_type=room.room_type,
                price=room.price,
                adult_capacity=adults,
                child_capacity=children
            )

            room.status = "Occupied"

            db.session.add(booking_room)

        payment = Accounting(
            transaction_no=transaction_no,
            booking_id=booking.id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            payment_status=payment_status,
            payment_method=payment_method
        )

        db.session.add(payment)
        db.session.commit()

        return redirect(url_for("admin.bookings"))

    return render_template(
        "admin/walkin_booking.html",
        available_rooms=available_rooms,
        today=datetime.today().strftime("%Y-%m-%d")
    )

@admin.route("/bookings/<int:booking_id>/delete")
@login_required
@role_required(["admin"])
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    for booked_room in booking.booking_rooms:
        room = Room.query.filter_by(
            room_number=booked_room.room_number
        ).first()

        if room:
            room.status = "Available"

    db.session.delete(booking)
    db.session.commit()

    return redirect(url_for("admin.bookings"))

@admin.route("/fix-room-status")
@login_required
@role_required(["admin"])
def fix_room_status():
    checked_out_bookings = Booking.query.filter_by(status="Checked Out").all()

    for booking in checked_out_bookings:
        for booked_room in booking.booking_rooms:
            room = Room.query.filter_by(
                room_number=booked_room.room_number
            ).first()

            if room:
                room.status = "Available"

    db.session.commit()

    return redirect(url_for("admin.rooms"))
