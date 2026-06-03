from functools import wraps

from flask import session, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("auth.staff_login"))

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