from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.models.user import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/staff-login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username, status="Active").first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["user_role"] = user.role

            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("auth/staff_login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.staff_login"))
