from app import db
from app.models.types import utc_now


class EquipmentIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    equipment_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Check Needed")
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    notes = db.Column(db.Text)
    reported_by = db.Column(db.String(50), nullable=False)
    maintenance_status = db.Column(
        db.String(40), nullable=False, default="Not Requested"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    room = db.relationship("Room", backref="equipment_issues")

