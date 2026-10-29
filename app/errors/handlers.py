from flask import render_template
from app.errors import errors_bp


@errors_bp.app_errorhandler(400)
def bad_request(error):
    return render_template("errors/400.html", error=error), 400


@errors_bp.app_errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", error=error), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    return render_template("errors/404.html", error=error), 404


@errors_bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template("errors/500.html", error=error), 500
