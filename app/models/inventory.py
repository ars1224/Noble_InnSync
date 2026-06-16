from datetime import datetime

from app import db


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(60), nullable=False, default="Guest Supplies")
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit = db.Column(db.String(30), nullable=False, default="items")
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return "Out of Stock"
        if self.current_stock <= self.reorder_level:
            return "Low Stock"
        return "OK"

