from flask import Blueprint, render_template
from app.models.room import Room

main = Blueprint("main", __name__)

@main.route("/")
def home():
    rooms = Room.query.all()
    return render_template("index.html", rooms = rooms)