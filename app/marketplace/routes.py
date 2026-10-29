from flask import render_template
from app.marketplace import marketplace_bp


@marketplace_bp.route("/")
def index():
    return render_template("marketplace/index.html")
