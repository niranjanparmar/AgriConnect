from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user


def farmer_required(f):
    """
    Decorator to restrict access strictly to authenticated Farmers.
    Rejects anonymous users by redirecting to login.
    Rejects authenticated consumers with HTTP 403 Forbidden.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in as a Farmer to access this portal.", "warning")
            return redirect(url_for("auth.login", next=request.path, role="farmer"))
        if not current_user.is_farmer:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def consumer_required(f):
    """
    Decorator to restrict access strictly to authenticated Consumers.
    Rejects anonymous users by redirecting to login.
    Rejects authenticated farmers with HTTP 403 Forbidden.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in as a Consumer to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path, role="consumer"))
        if not current_user.is_consumer:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
