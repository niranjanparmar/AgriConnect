from flask import render_template
from app.orders import orders_bp


@orders_bp.route("/cart")
def cart():
    return render_template("orders/cart.html")
