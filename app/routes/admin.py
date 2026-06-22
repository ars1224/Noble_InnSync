from flask import Blueprint, render_template, redirect, url_for, request, session

from app import db
from app.models.booking import Booking
from app.models.room import Room
from app.models.accounting import Accounting
from app.utils.auth import login_required, role_required
from datetime import datetime
from collections import Counter, defaultdict
from app.models.booking_room import BookingRoom
from app.models.inventory import InventoryItem
from app.models.equipment import EquipmentIssue
from app.models.activity_log import ActivityLog
from app.utils.pricing import calculate_nights, calculate_stay_total


admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/dashboard")
@login_required
def dashboard():
    today = datetime.today().strftime("%Y-%m-%d")
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    all_payments = Accounting.query.order_by(Accounting.created_at.desc()).all()
    all_rooms = Room.query.order_by(Room.room_number.asc()).all()

    arrivals_today = [
        booking for booking in all_bookings
        if booking.check_in == today
        and booking.status in ["Pending", "Confirmed", "Checked In"]
    ]
    departures_today = [
        booking for booking in all_bookings
        if booking.check_out == today
        and booking.status in ["Checked In", "Checked Out"]
    ]
    upcoming_arrivals_count = len([
        booking for booking in all_bookings
        if booking.check_in >= today
        and booking.status in ["Pending", "Confirmed"]
    ])

    pending_bookings = sum(
        booking.status == "Pending" for booking in all_bookings
    )
    in_house_bookings = sum(
        booking.status == "Checked In" for booking in all_bookings
    )

    room_status_counts = Counter(
        "Reserved" if room.status == "Booked" else room.status
        for room in all_rooms
    )
    total_rooms = len(all_rooms)
    available_rooms = room_status_counts.get("Available", 0)
    reserved_rooms = room_status_counts.get("Reserved", 0)
    occupied_rooms = room_status_counts.get("Occupied", 0)
    maintenance_rooms = room_status_counts.get("Maintenance", 0)
    occupancy_rate = (
        round((occupied_rooms / total_rooms) * 100)
        if total_rooms else 0
    )

    paid_transactions = [
        payment for payment in all_payments
        if payment.payment_status == "Paid"
    ]
    unpaid_transactions = [
        payment for payment in all_payments
        if payment.payment_status == "Unpaid"
    ]
    total_revenue = sum(payment.total_price for payment in paid_transactions)
    outstanding_revenue = sum(
        payment.total_price for payment in unpaid_transactions
    )

    attention_items = [
        {
            "label": "Pending bookings",
            "count": pending_bookings,
            "detail": "Need confirmation or cancellation",
            "class_name": "warning",
            "endpoint": "admin.bookings",
            "roles": ["admin", "staff"]
        },
        {
            "label": "Unpaid bookings",
            "count": len(unpaid_transactions),
            "detail": f"${outstanding_revenue:.2f} outstanding",
            "class_name": "danger",
            "endpoint": "admin.payments",
            "roles": ["admin", "manager"]
        },
        {
            "label": "Maintenance rooms",
            "count": maintenance_rooms,
            "detail": "Unavailable for new guests",
            "class_name": "neutral",
            "endpoint": "admin.rooms",
            "roles": ["admin", "staff"]
        }
    ]

    low_stock_count = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.reorder_level
    ).count()
    equipment_issue_count = EquipmentIssue.query.filter(
        EquipmentIssue.status != "Working"
    ).count()
    pending_alert_count = ActivityLog.query.filter(
        ActivityLog.delivery_status.in_(["Pending", "Failed"])
    ).count()

    attention_items.extend([
        {
            "label": "Low-stock items",
            "count": low_stock_count,
            "detail": "Inventory needs replenishment",
            "class_name": "warning",
            "endpoint": "admin.inventory",
            "roles": ["admin", "staff", "manager"]
        },
        {
            "label": "Equipment issues",
            "count": equipment_issue_count,
            "detail": "Rooms or assets need follow-up",
            "class_name": "danger",
            "endpoint": "admin.equipment",
            "roles": ["admin", "staff", "manager"]
        },
        {
            "label": "Pending alerts",
            "count": pending_alert_count,
            "detail": "Activity messages waiting to send",
            "class_name": "neutral",
            "endpoint": "admin.activity_log",
            "roles": ["admin", "staff", "manager"]
        }
    ])

    recent_bookings = all_bookings[:6]

    return render_template(
        "admin/dashboard.html",
        today=datetime.today(),
        arrivals_today=arrivals_today,
        departures_today=departures_today,
        upcoming_arrivals_count=upcoming_arrivals_count,
        pending_bookings=pending_bookings,
        in_house_bookings=in_house_bookings,
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        reserved_rooms=reserved_rooms,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms,
        occupancy_rate=occupancy_rate,
        total_revenue=total_revenue,
        low_stock_count=low_stock_count,
        equipment_issue_count=equipment_issue_count,
        pending_alert_count=pending_alert_count,
        outstanding_revenue=outstanding_revenue,
        paid_payments=len(paid_transactions),
        unpaid_payments=len(unpaid_transactions),
        attention_items=attention_items,
        recent_bookings=recent_bookings
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
    low_stock_items = [
        item for item in items
        if item.stock_status in ["Low Stock", "Out of Stock"]
    ]
    out_of_stock_count = sum(item.stock_status == "Out of Stock" for item in items)
    ok_stock_count = sum(item.stock_status == "OK" for item in items)
    low_stock_count = len(low_stock_items)
    inventory_health = round((ok_stock_count / len(items)) * 100) if items else 0
    category_counts = Counter(item.category for item in items)
    alerts_sent = ActivityLog.query.filter_by(
        event_type="Inventory", delivery_status="Sent"
    ).count()

    return render_template(
        "admin/inventory.html",
        items=items,
        low_stock_items=low_stock_items,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        ok_stock_count=ok_stock_count,
        inventory_health=inventory_health,
        category_counts=category_counts,
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
    item_name = request.form.get("item_name", item.item_name).strip()
    duplicate = InventoryItem.query.filter(
        InventoryItem.item_name == item_name,
        InventoryItem.id != item.id
    ).first()

    if item_name and not duplicate:
        item.item_name = item_name

    item.category = request.form.get("category", item.category).strip() or item.category
    item.unit = request.form.get("unit", item.unit).strip() or item.unit
    item.current_stock = max(
        0, request.form.get("current_stock", item.current_stock, type=int)
    )
    item.reorder_level = max(
        0, request.form.get("reorder_level", item.reorder_level, type=int)
    )
    add_activity(
        "Inventory",
        f"{item.item_name} inventory record updated to {item.current_stock} {item.unit}.",
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
    open_issues = [issue for issue in issues if issue.status != "Working"]
    high_priority_count = sum(issue.priority == "High" for issue in open_issues)
    maintenance_requested_count = sum(
        issue.maintenance_status == "Requested" for issue in issues
    )
    resolved_count = sum(issue.status == "Working" for issue in issues)
    return render_template(
        "admin/equipment.html",
        issues=issues,
        rooms=rooms,
        open_issues=len(open_issues),
        high_priority_count=high_priority_count,
        maintenance_requested_count=maintenance_requested_count,
        resolved_count=resolved_count,
    )


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
    status_counts = Counter(activity.delivery_status for activity in activities)
    type_counts = Counter(activity.event_type for activity in activities)
    return render_template(
        "admin/activity_log.html",
        activities=activities,
        sent_count=status_counts.get("Sent", 0),
        pending_count=status_counts.get("Pending", 0),
        failed_count=status_counts.get("Failed", 0),
        inventory_activity_count=type_counts.get("Inventory", 0),
        equipment_activity_count=type_counts.get("Equipment", 0),
    )


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
    total_rooms = len(all_rooms)
    available_rooms = sum(room.status == "Available" for room in all_rooms)
    reserved_rooms = sum(room.status in ["Reserved", "Booked"] for room in all_rooms)
    occupied_rooms = sum(room.status == "Occupied" for room in all_rooms)
    maintenance_rooms = sum(room.status == "Maintenance" for room in all_rooms)
    occupancy_rate = round((occupied_rooms / total_rooms) * 100) if total_rooms else 0

    return render_template(
        "admin/rooms.html",
        rooms=all_rooms,
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        reserved_rooms=reserved_rooms,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms,
        occupancy_rate=occupancy_rate
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
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    all_payments = Accounting.query.order_by(Accounting.created_at.desc()).all()
    all_rooms = Room.query.order_by(Room.room_number.asc()).all()

    total_bookings = len(all_bookings)
    active_bookings = [
        booking for booking in all_bookings
        if booking.status != "Cancelled"
    ]

    paid_transactions = [
        payment for payment in all_payments
        if payment.payment_status == "Paid"
    ]
    unpaid_transactions = [
        payment for payment in all_payments
        if payment.payment_status == "Unpaid"
    ]
    refunded_transactions = [
        payment for payment in all_payments
        if payment.payment_status == "Refunded"
    ]

    total_revenue = sum(payment.total_price for payment in paid_transactions)
    outstanding_revenue = sum(payment.total_price for payment in unpaid_transactions)
    gross_booking_value = sum(booking.total_price for booking in active_bookings)
    average_booking_value = (
        gross_booking_value / len(active_bookings)
        if active_bookings else 0
    )
    collectible_total = total_revenue + outstanding_revenue
    collection_rate = (
        round((total_revenue / collectible_total) * 100)
        if collectible_total else 0
    )

    booking_status_counts = Counter(booking.status for booking in all_bookings)
    booking_status_order = [
        ("Pending", "status-pending"),
        ("Confirmed", "status-confirmed"),
        ("Checked In", "status-checked-in"),
        ("Checked Out", "status-checked-out"),
        ("Cancelled", "status-cancelled"),
    ]
    booking_status_report = [
        {
            "label": status,
            "count": booking_status_counts.get(status, 0),
            "percentage": round(
                (booking_status_counts.get(status, 0) / total_bookings) * 100
            ) if total_bookings else 0,
            "class_name": class_name
        }
        for status, class_name in booking_status_order
    ]

    room_status_counts = Counter(
        "Reserved" if room.status == "Booked" else room.status
        for room in all_rooms
    )
    total_rooms = len(all_rooms)
    occupied_rooms = room_status_counts.get("Occupied", 0)
    available_rooms = room_status_counts.get("Available", 0)
    reserved_rooms = room_status_counts.get("Reserved", 0)
    maintenance_rooms = room_status_counts.get("Maintenance", 0)
    occupancy_rate = (
        round((occupied_rooms / total_rooms) * 100)
        if total_rooms else 0
    )

    room_type_data = defaultdict(lambda: {
        "inventory": 0,
        "available": 0,
        "reserved": 0,
        "occupied": 0,
        "maintenance": 0,
        "booking_ids": set(),
        "room_nights": 0,
        "booked_value": 0
    })

    for room in all_rooms:
        data = room_type_data[room.room_type]
        normalized_status = "Reserved" if room.status == "Booked" else room.status
        data["inventory"] += 1
        status_key = normalized_status.lower()
        if status_key in ["available", "reserved", "occupied", "maintenance"]:
            data[status_key] += 1

    for booking in active_bookings:
        try:
            nights = calculate_nights(booking.check_in, booking.check_out)
        except ValueError:
            nights = 0

        for booked_room in booking.booking_rooms:
            data = room_type_data[booked_room.room_type]
            data["booking_ids"].add(booking.id)
            data["room_nights"] += nights
            data["booked_value"] += booked_room.price * nights

    room_type_report = []
    for room_type, data in sorted(room_type_data.items()):
        room_type_report.append({
            "room_type": room_type,
            "inventory": data["inventory"],
            "available": data["available"],
            "reserved": data["reserved"],
            "occupied": data["occupied"],
            "maintenance": data["maintenance"],
            "bookings": len(data["booking_ids"]),
            "room_nights": data["room_nights"],
            "booked_value": data["booked_value"],
        })

    recent_transactions = all_payments[:8]

    return render_template(
        "admin/reports.html",
        total_bookings=total_bookings,
        paid_payments=len(paid_transactions),
        unpaid_payments=len(unpaid_transactions),
        refunded_payments=len(refunded_transactions),
        total_revenue=total_revenue,
        outstanding_revenue=outstanding_revenue,
        gross_booking_value=gross_booking_value,
        average_booking_value=average_booking_value,
        collection_rate=collection_rate,
        booking_status_report=booking_status_report,
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        reserved_rooms=reserved_rooms,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms,
        occupancy_rate=occupancy_rate,
        room_type_report=room_type_report,
        recent_transactions=recent_transactions,
        generated_at=datetime.now()
    )


@admin.route("/bookings/<int:booking_id>/approve")
@login_required
@role_required(["admin", "staff"])
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "Confirmed"

    for booked_room in booking.booking_rooms:
        room = Room.query.filter_by(room_number=booked_room.room_number).first()
        if room and room.status != "Occupied":
            room.status = "Reserved"

    db.session.commit()

    return redirect(url_for("admin.bookings"))


@admin.route("/bookings/<int:booking_id>/cancel")
@login_required
@role_required(["admin", "staff"])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "Cancelled"

    for booked_room in booking.booking_rooms:
        room = Room.query.filter_by(room_number=booked_room.room_number).first()
        if room:
            room.status = "Available"

    db.session.commit()

    return redirect(url_for("admin.bookings"))


@admin.route("/rooms/<int:room_id>/update-status", methods=["POST"])
@login_required
@role_required(["admin", "staff"])
def update_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    new_status = request.form.get("status")

    if new_status in ["Available", "Reserved", "Occupied", "Maintenance"]:
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
    allowed_methods = ["Pay on Arrival", "Card", "Cash"]

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
    payment = booking.accounting[0] if booking.accounting else None
    nightly_total = sum(room.price for room in booking.booking_rooms)

    try:
        nights = calculate_nights(booking.check_in, booking.check_out)
    except ValueError:
        nights = 0

    return render_template(
        "admin/booking_details.html",
        booking=booking,
        payment=payment,
        nightly_total=nightly_total,
        nights=nights
    )

@admin.route("/bookings/<int:booking_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["admin", "staff"])
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    allowed_statuses = (
        "Pending",
        "Confirmed",
        "Checked In",
        "Checked Out",
        "Cancelled"
    )
    nightly_total = sum(room.price for room in booking.booking_rooms)

    def render_edit_form(form_values=None, form_errors=None, status_code=200):
        if form_values is None:
            form_values = {
                "guest_name": booking.guest_name,
                "email": booking.email,
                "phone": booking.phone,
                "check_in": booking.check_in,
                "check_out": booking.check_out,
                "adults": booking.adults,
                "children": booking.children,
                "status": booking.status
            }

        try:
            preview_nights, preview_room_total = calculate_stay_total(
                nightly_total,
                form_values["check_in"],
                form_values["check_out"]
            )
            preview_total = round(preview_room_total * 1.15, 2)
        except ValueError:
            preview_nights = 0
            preview_total = 0

        rendered_page = render_template(
            "admin/edit_booking.html",
            booking=booking,
            form_values=form_values,
            form_errors=form_errors or [],
            allowed_statuses=allowed_statuses,
            nightly_total=nightly_total,
            preview_nights=preview_nights,
            preview_total=preview_total
        )
        return rendered_page, status_code

    if request.method == "POST":
        form_values = {
            "guest_name": request.form.get("guest_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "check_in": request.form.get("check_in", "").strip(),
            "check_out": request.form.get("check_out", "").strip(),
            "adults": request.form.get("adults", "").strip(),
            "children": request.form.get("children", "").strip(),
            "status": request.form.get("status", "").strip()
        }
        form_errors = []

        if not form_values["guest_name"]:
            form_errors.append("Guest name is required.")

        if not form_values["email"] or "@" not in form_values["email"]:
            form_errors.append("Enter a valid guest email address.")

        if not form_values["phone"]:
            form_errors.append("Phone number is required.")

        try:
            adults = int(form_values["adults"])
            if adults < 1:
                raise ValueError
        except (TypeError, ValueError):
            adults = None
            form_errors.append("Adults must be at least 1.")

        try:
            children = int(form_values["children"])
            if children < 0:
                raise ValueError
        except (TypeError, ValueError):
            children = None
            form_errors.append("Children cannot be negative.")

        if form_values["status"] not in allowed_statuses:
            form_errors.append("Choose a valid booking status.")

        try:
            nights, room_total = calculate_stay_total(
                nightly_total,
                form_values["check_in"],
                form_values["check_out"]
            )
            total_price = round(room_total * 1.15, 2)
        except ValueError as error:
            nights = None
            total_price = None
            form_errors.append(str(error))

        if form_errors:
            return render_edit_form(form_values, form_errors, 400)

        booking.guest_name = form_values["guest_name"]
        booking.email = form_values["email"]
        booking.phone = form_values["phone"]
        booking.check_in = form_values["check_in"]
        booking.check_out = form_values["check_out"]
        booking.adults = adults
        booking.children = children
        booking.total_price = total_price
        booking.status = form_values["status"]

        room_status = {
            "Pending": "Reserved",
            "Confirmed": "Reserved",
            "Checked In": "Occupied",
            "Checked Out": "Available",
            "Cancelled": "Available"
        }[booking.status]

        for booked_room in booking.booking_rooms:
            room = Room.query.filter_by(
                room_number=booked_room.room_number
            ).first()
            if room:
                room.status = room_status

        for payment in booking.accounting:
            payment.check_in = booking.check_in
            payment.check_out = booking.check_out
            payment.total_price = booking.total_price

        db.session.commit()

        return redirect(url_for("admin.booking_details", booking_id=booking.id))

    return render_edit_form()

@admin.route("/bookings/<int:booking_id>/payment", methods=["GET", "POST"])
@login_required
@role_required(["admin", "staff", "manager"])
def booking_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment = Accounting.query.filter_by(booking_id=booking.id).first()
    allowed_statuses = ("Unpaid", "Paid", "Refunded")
    allowed_methods = ("Pay on Arrival", "Card", "Cash")

    try:
        nights = calculate_nights(booking.check_in, booking.check_out)
    except ValueError:
        nights = 0

    nightly_total = sum(room.price for room in booking.booking_rooms)

    def render_payment_form(form_values=None, form_errors=None, status_code=200):
        if form_values is None:
            form_values = {
                "payment_status": (
                    payment.payment_status if payment else "Unpaid"
                ),
                "payment_method": (
                    payment.payment_method if payment else "Pay on Arrival"
                )
            }

        rendered_page = render_template(
            "admin/booking_payment.html",
            booking=booking,
            payment=payment,
            form_values=form_values,
            form_errors=form_errors or [],
            allowed_statuses=allowed_statuses,
            allowed_methods=allowed_methods,
            nightly_total=nightly_total,
            nights=nights
        )
        return rendered_page, status_code

    if request.method == "POST":
        form_values = {
            "payment_status": request.form.get("payment_status", "").strip(),
            "payment_method": request.form.get("payment_method", "").strip()
        }
        form_errors = []

        if form_values["payment_status"] not in allowed_statuses:
            form_errors.append("Choose a valid payment status.")

        if form_values["payment_method"] not in allowed_methods:
            form_errors.append("Choose a valid payment method.")

        if form_errors:
            return render_payment_form(form_values, form_errors, 400)

        if payment:
            payment.payment_status = form_values["payment_status"]
            payment.payment_method = form_values["payment_method"]
            payment.check_in = booking.check_in
            payment.check_out = booking.check_out
            payment.total_price = booking.total_price
        else:
            payment = Accounting(
                transaction_no=f"TXN-{booking.reference_number}",
                booking_id=booking.id,
                check_in=booking.check_in,
                check_out=booking.check_out,
                total_price=booking.total_price,
                payment_status=form_values["payment_status"],
                payment_method=form_values["payment_method"]
            )
            db.session.add(payment)

        db.session.commit()

        return redirect(
            url_for("admin.booking_details", booking_id=booking.id)
        )

    return render_payment_form()

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

        nightly_total = sum(room.price for room in valid_rooms)

        try:
            nights, room_total = calculate_stay_total(
                nightly_total,
                check_in,
                check_out
            )
            total_price = round(room_total * 1.15, 2)
        except ValueError as error:
            return str(error), 400

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
