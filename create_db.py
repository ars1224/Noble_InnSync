from app import create_app, db
from app.models.room import Room
from app.models.booking import Booking

app = create_app()

with app.app_context():

    db.create_all()

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
