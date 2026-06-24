from functools import wraps

from flask import session, redirect, url_for
from app import db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.staff_login"))

        from app.models.user import User

        user = db.session.get(User, user_id)
        if not user or user.status != "Active":
            session.clear()
            return redirect(url_for("auth.staff_login"))

        session["username"] = user.username
        session["user_role"] = user.role

        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles):
    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            if "user_role" not in session:
                return redirect(url_for("auth.staff_login"))

            if session["user_role"] not in allowed_roles:
             return redirect(url_for("admin.access_denied"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator
