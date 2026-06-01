from app import create_app, db
from app.models.room import Room

app = create_app()

with app.app_context():
    db.create_all()

    defaults = {
        '101': ('Single Room', 149, 'Available'),
        '102': ('Double Room', 229, 'Available'),
        '103': ('Family Room', 329, 'Occupied'),
    }

    if Room.query.count() == 0:
        rooms = [
            Room(room_number=number, room_type=room_type, price=price, status=status)
            for number, (room_type, price, status) in defaults.items()
        ]
        db.session.add_all(rooms)
        db.session.commit()
    else:
        for room in Room.query.all():
            if room.room_number in defaults:
                room.room_type = defaults[room.room_number][0]
                room.price = defaults[room.room_number][1]
                room.status = defaults[room.room_number][2]
        db.session.commit()

    print('Database created successfully.')
