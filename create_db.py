from app import create_app, db
from app.models.room import Room

app = create_app()

with app.app_context():
    db.create_all()

    defaults = {
        '101': ('Single Room', 149, 'Available'),
        '102': ('Single Room', 149, 'Available'),
        '103': ('Single Room', 159, 'Available'),
        '104': ('Single Room', 159, 'Unavailable'),
        '201': ('Double Room', 229, 'Available'),
        '202': ('Double Room', 229, 'Available'),
        '203': ('Double Room', 249, 'Unavailable'),
        '204': ('Double Room', 249, 'Available'),
        '301': ('Family Room', 329, 'Available'),
        '302': ('Family Room', 329, 'Unavailable'),
        '303': ('Family Room', 349, 'Available'),
        '304': ('Family Room', 349, 'Available'),
    }

    if Room.query.count() == 0:
        rooms = [
            Room(room_number=number, room_type=room_type, price=price, status=status)
            for number, (room_type, price, status) in defaults.items()
        ]
        db.session.add_all(rooms)
        db.session.commit()
    else:
        existing_rooms = {
            room.room_number: room
            for room in Room.query.all()
        }

        for number, (room_type, price, status) in defaults.items():
            if number in existing_rooms:
                existing_rooms[number].room_type = room_type
                existing_rooms[number].price = price
                existing_rooms[number].status = status
            else:
                db.session.add(
                    Room(room_number=number, room_type=room_type, price=price, status=status)
                )
        db.session.commit()

    print('Database created successfully.')
