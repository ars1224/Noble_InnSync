from datetime import date, datetime, timedelta

from app import create_app, db
from app.models.accounting import Accounting
from app.models.activity_log import ActivityLog
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.equipment import EquipmentIssue
from app.models.inventory import InventoryItem
from app.models.room import Room
from app.utils.pricing import calculate_stay_total

app = create_app()

ROOM_DEFAULTS = {
    "101": (
        "Single Room",
        "Quiet first-floor room for solo guests, with a work desk and garden outlook.",
        149,
    ),
    "102": (
        "Single Room",
        "Compact solo room near reception, ideal for short business stays.",
        149,
    ),
    "103": (
        "Single Room",
        "Light-filled single room with courtyard views and easy lift access.",
        149,
    ),
    "104": (
        "Single Room",
        "Private single room tucked away from the main corridor for a quieter stay.",
        149,
    ),
    "105": (
        "Single Room",
        "Solo guest room with blackout curtains, a writing desk, and fast Wi-Fi.",
        149,
    ),
    "201": (
        "Double Room",
        "Modern double room with a queen bed, lounge chair, and city-facing windows.",
        229,
    ),
    "202": (
        "Double Room",
        "Spacious couple-friendly room with extra storage and an ensuite bathroom.",
        229,
    ),
    "203": (
        "Double Room",
        "Comfortable double room close to the lift, suited to weekend getaways.",
        229,
    ),
    "204": (
        "Double Room",
        "Upper-floor double room with a reading nook and filtered afternoon sun.",
        229,
    ),
    "205": (
        "Double Room",
        "Double room currently set aside for maintenance follow-up.",
        229,
    ),
    "301": (
        "Family Room",
        "Large family room with flexible bedding and space for luggage or a cot.",
        329,
    ),
    "302": (
        "Family Room",
        "Family room with two sleeping zones, ideal for longer stays.",
        329,
    ),
    "303": (
        "Family Room",
        "Roomy family suite near the end of the hallway for groups wanting privacy.",
        329,
    ),
    "304": (
        "Family Room",
        "Bright family suite with sofa seating and a generous ensuite.",
        329,
    ),
    "305": (
        "Family Room",
        "Top-floor family room with extra bedding options and storage.",
        329,
    ),
}

ROOM_CAPACITY = {
    "Single Room": (1, 0),
    "Double Room": (2, 1),
    "Family Room": (4, 2),
}

INVENTORY_SEED = [
    ("Bath Towels", "Guest Supplies", 18, 24, "pieces"),
    ("Hand Soap", "Guest Supplies", 42, 20, "bottles"),
    ("Shampoo", "Guest Supplies", 14, 18, "bottles"),
    ("Conditioner", "Guest Supplies", 11, 18, "bottles"),
    ("Toilet Paper", "Housekeeping", 32, 30, "rolls"),
    ("Bed Sheets", "Housekeeping", 16, 18, "sets"),
    ("Pillow Cases", "Housekeeping", 44, 36, "pieces"),
    ("Laundry Detergent", "Housekeeping", 5, 8, "containers"),
    ("Coffee Sachets", "Food and Beverage", 64, 40, "sachets"),
    ("Tea Bags", "Food and Beverage", 72, 40, "bags"),
    ("Milk Portions", "Food and Beverage", 26, 30, "portions"),
    ("Mini Bar Water", "Food and Beverage", 48, 24, "bottles"),
    ("Key Cards", "Front Office", 21, 30, "cards"),
    ("Printer Paper", "Front Office", 7, 10, "reams"),
]

def iso(day):
    return day.strftime("%Y-%m-%d")


def upsert_inventory():
    for item_name, category, stock, reorder_level, unit in INVENTORY_SEED:
        item = InventoryItem.query.filter_by(item_name=item_name).first()
        if not item:
            item = InventoryItem(item_name=item_name)
            db.session.add(item)

        item.category = category
        item.current_stock = stock
        item.reorder_level = reorder_level
        item.unit = unit


def upsert_rooms():
    for room_number, (room_type, description, price) in ROOM_DEFAULTS.items():
        room = Room.query.filter_by(room_number=room_number).first()
        if not room:
            room = Room(room_number=room_number)
            db.session.add(room)

        room.room_type = room_type
        room.description = description
        room.price = price
        room.status = "Available"


def clear_demo_activity_and_issues():
    ActivityLog.query.filter_by(created_by="seed").delete()
    EquipmentIssue.query.filter(
        EquipmentIssue.reported_by.in_(["Mia Clarke", "Samira Khan", "Jordan Lee"])
    ).delete(synchronize_session=False)


def room_status_for_booking(status):
    if status in ("Pending", "Confirmed"):
        return "Reserved"
    if status == "Checked In":
        return "Occupied"
    return "Available"


def upsert_booking(seed):
    booking = Booking.query.filter_by(
        reference_number=seed["reference_number"]
    ).first()
    if not booking:
        booking = Booking(reference_number=seed["reference_number"])
        db.session.add(booking)
    else:
        BookingRoom.query.filter_by(booking_id=booking.id).delete()
        Accounting.query.filter_by(booking_id=booking.id).delete()

    check_in = iso(seed["check_in"])
    check_out = iso(seed["check_out"])
    nightly_total = sum(ROOM_DEFAULTS[number][2] for number in seed["rooms"])
    nights, total_price = calculate_stay_total(nightly_total, check_in, check_out)

    booking.guest_name = seed["guest_name"]
    booking.email = seed["email"]
    booking.phone = seed["phone"]
    booking.check_in = check_in
    booking.check_out = check_out
    booking.adults = seed["adults"]
    booking.children = seed["children"]
    booking.total_price = total_price
    booking.status = seed["status"]
    booking.created_at = seed["created_at"]
    db.session.flush()

    for room_number in seed["rooms"]:
        room_type = ROOM_DEFAULTS[room_number][0]
        adult_capacity, child_capacity = ROOM_CAPACITY[room_type]
        db.session.add(
            BookingRoom(
                booking_id=booking.id,
                room_number=room_number,
                room_type=room_type,
                price=ROOM_DEFAULTS[room_number][2],
                adult_capacity=adult_capacity,
                child_capacity=child_capacity,
            )
        )

        room = Room.query.filter_by(room_number=room_number).first()
        if room and seed["status"] in ("Pending", "Confirmed", "Checked In"):
            room.status = room_status_for_booking(seed["status"])

    db.session.add(
        Accounting(
            transaction_no=seed["transaction_no"],
            booking_id=booking.id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            payment_status=seed["payment_status"],
            payment_method=seed["payment_method"],
            created_at=seed["created_at"] + timedelta(minutes=12),
        )
    )

    return nights, total_price


def seed_bookings(today):
    created_base = datetime.combine(today - timedelta(days=18), datetime.min.time())
    booking_seeds = [
        {
            "reference_number": "NIS-DEMO-1001",
            "transaction_no": "TXN-DEMO-1001",
            "guest_name": "Priya Singh",
            "email": "priya.singh@example.com",
            "phone": "+64 21 555 013",
            "check_in": today - timedelta(days=1),
            "check_out": today + timedelta(days=1),
            "adults": 1,
            "children": 0,
            "rooms": ["101"],
            "status": "Checked In",
            "payment_status": "Paid",
            "payment_method": "Card Payment",
            "created_at": created_base + timedelta(days=1, hours=9),
        },
        {
            "reference_number": "NIS-DEMO-1002",
            "transaction_no": "TXN-DEMO-1002",
            "guest_name": "Liam Nguyen",
            "email": "liam.nguyen@example.com",
            "phone": "+64 22 555 018",
            "check_in": today,
            "check_out": today + timedelta(days=2),
            "adults": 2,
            "children": 0,
            "rooms": ["202"],
            "status": "Checked In",
            "payment_status": "Paid",
            "payment_method": "EFTPOS",
            "created_at": created_base + timedelta(days=4, hours=14),
        },
        {
            "reference_number": "NIS-DEMO-1003",
            "transaction_no": "TXN-DEMO-1003",
            "guest_name": "Emma Brown",
            "email": "emma.brown@example.com",
            "phone": "+64 27 555 021",
            "check_in": today - timedelta(days=2),
            "check_out": today,
            "adults": 4,
            "children": 2,
            "rooms": ["301", "302"],
            "status": "Checked In",
            "payment_status": "Paid",
            "payment_method": "Cash",
            "created_at": created_base + timedelta(days=5, hours=10),
        },
        {
            "reference_number": "NIS-DEMO-1004",
            "transaction_no": "TXN-DEMO-1004",
            "guest_name": "Oliver Williams",
            "email": "oliver.williams@example.com",
            "phone": "+64 21 555 044",
            "check_in": today + timedelta(days=2),
            "check_out": today + timedelta(days=5),
            "adults": 2,
            "children": 1,
            "rooms": ["203"],
            "status": "Confirmed",
            "payment_status": "Unpaid",
            "payment_method": "Pay on Arrival",
            "created_at": created_base + timedelta(days=7, hours=11),
        },
        {
            "reference_number": "NIS-DEMO-1005",
            "transaction_no": "TXN-DEMO-1005",
            "guest_name": "Aroha Patel",
            "email": "aroha.patel@example.com",
            "phone": "+64 20 555 067",
            "check_in": today + timedelta(days=5),
            "check_out": today + timedelta(days=7),
            "adults": 1,
            "children": 0,
            "rooms": ["102"],
            "status": "Pending",
            "payment_status": "Unpaid",
            "payment_method": "Pay on Arrival",
            "created_at": created_base + timedelta(days=11, hours=8),
        },
        {
            "reference_number": "NIS-DEMO-1006",
            "transaction_no": "TXN-DEMO-1006",
            "guest_name": "Sofia Garcia",
            "email": "sofia.garcia@example.com",
            "phone": "+64 29 555 084",
            "check_in": today + timedelta(days=10),
            "check_out": today + timedelta(days=12),
            "adults": 2,
            "children": 0,
            "rooms": ["201"],
            "status": "Confirmed",
            "payment_status": "Paid",
            "payment_method": "Bank Transfer",
            "created_at": created_base + timedelta(days=13, hours=16),
        },
        {
            "reference_number": "NIS-DEMO-1007",
            "transaction_no": "TXN-DEMO-1007",
            "guest_name": "Noah Thompson",
            "email": "noah.thompson@example.com",
            "phone": "+64 21 555 092",
            "check_in": today - timedelta(days=6),
            "check_out": today - timedelta(days=3),
            "adults": 2,
            "children": 2,
            "rooms": ["303"],
            "status": "Checked Out",
            "payment_status": "Paid",
            "payment_method": "Card Payment",
            "created_at": created_base + timedelta(days=2, hours=13),
        },
        {
            "reference_number": "NIS-DEMO-1008",
            "transaction_no": "TXN-DEMO-1008",
            "guest_name": "Grace Taylor",
            "email": "grace.taylor@example.com",
            "phone": "+64 22 555 102",
            "check_in": today - timedelta(days=12),
            "check_out": today - timedelta(days=9),
            "adults": 1,
            "children": 0,
            "rooms": ["104"],
            "status": "Checked Out",
            "payment_status": "Paid",
            "payment_method": "Card Payment",
            "created_at": created_base + timedelta(hours=15),
        },
        {
            "reference_number": "NIS-DEMO-1009",
            "transaction_no": "TXN-DEMO-1009",
            "guest_name": "Ethan Wilson",
            "email": "ethan.wilson@example.com",
            "phone": "+64 27 555 119",
            "check_in": today + timedelta(days=3),
            "check_out": today + timedelta(days=4),
            "adults": 2,
            "children": 0,
            "rooms": ["204"],
            "status": "Cancelled",
            "payment_status": "Refunded",
            "payment_method": "Card Payment",
            "created_at": created_base + timedelta(days=8, hours=17),
        },
        {
            "reference_number": "NIS-DEMO-1010",
            "transaction_no": "TXN-DEMO-1010",
            "guest_name": "Mei Chen",
            "email": "mei.chen@example.com",
            "phone": "+64 20 555 130",
            "check_in": today + timedelta(days=1),
            "check_out": today + timedelta(days=4),
            "adults": 3,
            "children": 1,
            "rooms": ["305"],
            "status": "Confirmed",
            "payment_status": "Unpaid",
            "payment_method": "Pay on Arrival",
            "created_at": created_base + timedelta(days=12, hours=12),
        },
    ]

    return [upsert_booking(seed) for seed in booking_seeds]


def seed_equipment(today):
    issue_seeds = [
        ("205", "Air conditioning unit", "Broken", "High",
         "Unit is blowing warm air and making a rattling sound.",
         "Samira Khan", "Requested", today - timedelta(days=1)),
        ("103", "Bedside lamp", "Check Needed", "Low",
         "Guest reported intermittent flickering during turndown.",
         "Mia Clarke", "Not Requested", today - timedelta(days=2)),
        ("301", "Bathroom extractor fan", "Check Needed", "Medium",
         "Fan is noisy after running for several minutes.",
         "Samira Khan", "Requested", today),
        ("202", "Mini fridge", "Working", "Low",
         "Temperature reset after guest query; monitoring complete.",
         "Jordan Lee", "Resolved", today - timedelta(days=4)),
    ]

    for room_number, equipment, status, priority, notes, reported_by, maintenance, day in issue_seeds:
        room = Room.query.filter_by(room_number=room_number).first()
        if not room:
            continue

        if status == "Broken":
            room.status = "Maintenance"

        db.session.add(
            EquipmentIssue(
                room_id=room.id,
                equipment_name=equipment,
                status=status,
                priority=priority,
                notes=notes,
                reported_by=reported_by,
                maintenance_status=maintenance,
                created_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=9),
                updated_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=11),
            )
        )


def seed_activity(today):
    activity_seeds = [
        (
            "Inventory",
            "Shampoo is below reorder level after morning housekeeping count.",
            "Pending",
            "manager",
            today,
        ),
        (
            "Inventory",
            "Key Cards are below reorder level; front office needs replenishment.",
            "Failed",
            "manager",
            today - timedelta(days=1),
        ),
        (
            "Equipment",
            "Room 205 air conditioning repair request sent to maintenance.",
            "Sent",
            "manager",
            today - timedelta(days=1),
        ),
        (
            "Booking",
            "Family booking NIS-DEMO-1003 is due to depart today.",
            "Sent",
            "staff",
            today,
        ),
        (
            "Payment",
            "Three upcoming bookings still have unpaid balances.",
            "Pending",
            "manager",
            today,
        ),
    ]

    for event_type, message, status, target_role, day in activity_seeds:
        db.session.add(
            ActivityLog(
                event_type=event_type,
                message=message,
                delivery_status=status,
                created_by="seed",
                target_role=target_role,
                created_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=8),
            )
        )


with app.app_context():
    db.create_all()

    today = date.today()

    upsert_inventory()
    upsert_rooms()
    db.session.commit()

    clear_demo_activity_and_issues()
    seed_bookings(today)
    seed_equipment(today)
    seed_activity(today)

    db.session.commit()

    print("Database created and seeded with realistic demo data.")
