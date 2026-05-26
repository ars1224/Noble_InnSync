from app import create_app, db
from app.models.room import Room

app = create_app()

with app.app_context():
    db.create_all()

    if Room.query.count() == 0:
        rooms = [
            Room(room_number="101", room_type="Single Room", price=1200, status="Available"),
            Room(room_number="102", room_type="Double Room", price=1800, status="Available"),
            Room(room_number="103", room_type="Family Room", price=2500, status="Occupied"),
        ]

        db.session.add_all(rooms)
        db.session.commit()

    print("Database created successfully.")