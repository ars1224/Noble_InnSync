from app import create_app, db

from app.models.room import Room
from app.models.booking import Booking
from app.models.booking_room import BookingRoom
from app.models.accounting import Accounting
from app.models.user import User
from app.models.inventory import InventoryItem
from app.models.equipment import EquipmentIssue
from app.models.activity_log import ActivityLog

app = create_app()

with app.app_context():

    db.create_all()

    default_inventory = [
        ("Bath Towels", "Guest Supplies", 8, 12, "pieces"),
        ("Hand Soap", "Guest Supplies", 36, 15, "bottles"),
        ("Shampoo", "Guest Supplies", 18, 15, "bottles"),
        ("Toilet Paper", "Housekeeping", 24, 20, "rolls"),
        ("Bed Sheets", "Housekeeping", 10, 12, "sets"),
        ("Coffee Sachets", "Food and Beverage", 42, 20, "sachets"),
    ]

    for item_name, category, stock, reorder_level, unit in default_inventory:
        if not InventoryItem.query.filter_by(item_name=item_name).first():
            db.session.add(InventoryItem(
                item_name=item_name,
                category=category,
                current_stock=stock,
                reorder_level=reorder_level,
                unit=unit,
            ))

    defaults = {

        # SINGLE ROOMS
        '101': (
            'Single Room',
            'Perfect for solo travelers seeking a cozy and affordable stay.',
            149,
            'Available'
        ),

        '102': (
            'Single Room',
            'Perfect for solo travelers seeking a cozy and affordable stay.',
            149,
            'Available'
        ),

        '103': (
            'Single Room',
            'Perfect for solo travelers seeking a cozy and affordable stay.',
            149,
            'Available'
        ),

        '104': (
            'Single Room',
            'Perfect for solo travelers seeking a cozy and affordable stay.',
            149,
            'Occupied'
        ),

        '105': (
            'Single Room',
            'Perfect for solo travelers seeking a cozy and affordable stay.',
            149,
            'Available'
        ),

        # DOUBLE ROOMS
        '201': (
            'Double Room',
            'Ideal for couples with spacious comfort and modern amenities.',
            229,
            'Available'
        ),

        '202': (
            'Double Room',
            'Ideal for couples with spacious comfort and modern amenities.',
            229,
            'Occupied'
        ),

        '203': (
            'Double Room',
            'Ideal for couples with spacious comfort and modern amenities.',
            229,
            'Available'
        ),

        '204': (
            'Double Room',
            'Ideal for couples with spacious comfort and modern amenities.',
            229,
            'Available'
        ),

        '205': (
            'Double Room',
            'Ideal for couples with spacious comfort and modern amenities.',
            229,
            'Maintenance'
        ),

        # FAMILY ROOMS
        '301': (
            'Family Room',
            'Designed for families and groups with extra space and comfort.',
            329,
            'Available'
        ),

        '302': (
            'Family Room',
            'Designed for families and groups with extra space and comfort.',
            329,
            'Available'
        ),

        '303': (
            'Family Room',
            'Designed for families and groups with extra space and comfort.',
            329,
            'Occupied'
        ),

        '304': (
            'Family Room',
            'Designed for families and groups with extra space and comfort.',
            329,
            'Occupied'
        ),

        '305': (
            'Family Room',
            'Designed for families and groups with extra space and comfort.',
            329,
            'Occupied'
        ),
    }

    default_users = [
        ("admin", "admin123", "admin", "System Admin"),
        ("staff", "staff123", "staff", "Staff User"),
        ("manager", "manager123", "manager", "Manager User")
    ]

    for username, password, role, full_name in default_users:
        existing_user = User.query.filter_by(username=username).first()

        if not existing_user:
            user = User(
                username=username,
                role=role,
                full_name=full_name
            )
            user.set_password(password)
            db.session.add(user)

    db.session.commit()

    if Room.query.count() == 0:

        rooms = [

            Room(
                room_number=number,
                room_type=room_type,
                description=description,
                price=price,
                status=status
            )

            for number, (room_type, description, price, status) in defaults.items()

        ]

        db.session.add_all(rooms)
        db.session.commit()

    else:

        for room in Room.query.all():

            if room.room_number in defaults:

                room.room_type = defaults[room.room_number][0]
                room.description = defaults[room.room_number][1]
                room.price = defaults[room.room_number][2]
                room.status = defaults[room.room_number][3]

        db.session.commit()

    print('Database created successfully.')
