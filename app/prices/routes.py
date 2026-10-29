from flask import render_template
from app.prices import prices_bp


@prices_bp.route("/")
def index():
    return render_template("prices/index.html")
