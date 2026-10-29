from flask import render_template, request, flash, redirect, url_for
from app.orders import orders_bp

# Demo cart items for Phase 3 UI walkthrough
DEMO_CART = [
    {
        "product_id": 1,
        "name": "Fresh Organic Sharbati Wheat",
        "farmer_name": "Ramesh Patel",
        "price": 42.00,
        "quantity": 25,
        "unit": "kg",
        "subtotal": 1050.00,
        "stock_available": 450,
        "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=200&q=80",
    },
    {
        "product_id": 4,
        "name": "Cold-Pressed Groundnut Oil",
        "farmer_name": "Kishore Solanki",
        "price": 210.00,
        "quantity": 2,
        "unit": "litre",
        "subtotal": 420.00,
        "stock_available": 65,
        "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=200&q=80",
    },
]

# Demo order history
DEMO_ORDERS = [
    {
        "id": 8921,
        "order_number": "AGC-2026-8921",
        "date": "28 Oct 2026",
        "total_amount": 1470.00,
        "status": "Confirmed",
        "payment_method": "Cash on Delivery",
        "delivery_address": "Flat 302, Green Park Residency, Kalawad Road, Rajkot, Gujarat - 360005",
        "items": DEMO_CART,
        "status_history": [
            {"step": "Order Placed", "time": "28 Oct, 09:30 AM", "done": True},
            {"step": "Farmer Confirmed", "time": "28 Oct, 11:15 AM", "done": True},
            {"step": "Dispatched / In Transit", "time": "Expected Tomorrow", "done": False},
            {"step": "Delivered", "time": "Pending", "done": False},
        ],
    },
    {
        "id": 8840,
        "order_number": "AGC-2026-8840",
        "date": "15 Oct 2026",
        "total_amount": 750.00,
        "status": "Delivered",
        "payment_method": "Cash on Delivery",
        "delivery_address": "Flat 302, Green Park Residency, Kalawad Road, Rajkot, Gujarat - 360005",
        "items": [DEMO_CART[0]],
        "status_history": [
            {"step": "Order Placed", "time": "15 Oct, 10:00 AM", "done": True},
            {"step": "Farmer Confirmed", "time": "15 Oct, 12:00 PM", "done": True},
            {"step": "Dispatched / In Transit", "time": "16 Oct, 02:00 PM", "done": True},
            {"step": "Delivered", "time": "17 Oct, 04:30 PM", "done": True},
        ],
    },
]


@orders_bp.route("/cart")
def cart():
    subtotal = sum(item["subtotal"] for item in DEMO_CART)
    delivery_fee = 50.00
    total = subtotal + delivery_fee
    return render_template("orders/cart.html", cart=DEMO_CART, subtotal=subtotal, delivery_fee=delivery_fee, total=total)


@orders_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    subtotal = sum(item["subtotal"] for item in DEMO_CART)
    delivery_fee = 50.00
    total = subtotal + delivery_fee

    if request.method == "POST":
        flash("Order placed successfully! Order ID: #AGC-2026-8922 (Demo Mode / Cash on Delivery).", "success")
        return redirect(url_for("orders.order_detail", order_id=8921))

    return render_template("orders/checkout.html", cart=DEMO_CART, subtotal=subtotal, delivery_fee=delivery_fee, total=total)


@orders_bp.route("/consumer/dashboard")
def consumer_dashboard():
    stats = {
        "active_orders": 1,
        "completed_orders": 3,
        "total_spent": 3840.00,
    }
    return render_template("orders/consumer_dashboard.html", stats=stats, recent_orders=DEMO_ORDERS)


@orders_bp.route("/history")
def order_history():
    return render_template("orders/order_history.html", orders=DEMO_ORDERS)


@orders_bp.route("/order/<int:order_id>")
def order_detail(order_id):
    order = next((o for o in DEMO_ORDERS if o["id"] == order_id), DEMO_ORDERS[0])
    return render_template("orders/order_detail.html", order=order)


@orders_bp.route("/farmer/orders", methods=["GET", "POST"])
def farmer_orders():
    if request.method == "POST":
        order_id = request.form.get("order_id")
        new_status = request.form.get("status")
        flash(f"Order #{order_id} status updated to '{new_status}' successfully.", "success")
        return redirect(url_for("orders.farmer_orders"))
    return render_template("orders/farmer_orders.html", orders=DEMO_ORDERS)
