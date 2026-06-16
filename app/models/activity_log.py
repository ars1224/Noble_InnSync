from datetime import datetime

from app import db


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(40), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    delivery_status = db.Column(db.String(30), nullable=False, default="Pending")
    created_by = db.Column(db.String(50), nullable=False)
    target_role = db.Column(db.String(30), nullable=False, default="manager")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

