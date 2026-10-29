import uuid
from decimal import Decimal
from datetime import datetime, timezone
from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.orders import orders_bp
from app.auth.decorators import consumer_required, farmer_required
from app.models.marketplace import ProduceListing, CartItem
from app.models.order import Order, DeliveryDetail, OrderItem


@orders_bp.route("/cart")
def cart():
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    else:
        cart_items = []

    subtotal = sum(item.subtotal for item in cart_items)
    delivery_fee = Decimal("50.00") if cart_items else Decimal("0.00")
    total = subtotal + delivery_fee

    return render_template(
        "orders/cart.html",
        cart=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
    )


@orders_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    if not current_user.is_authenticated:
        flash("Please log in as a Consumer to add items to your cart.", "info")
        return redirect(url_for("auth.login", next=request.referrer or url_for("marketplace.index"), role="consumer"))

    if current_user.is_farmer:
        flash("Farmers cannot purchase produce. Please switch to a consumer account to buy harvest.", "warning")
        return redirect(url_for("marketplace.index"))

    listing_id = request.form.get("listing_id", type=int)
    quantity = request.form.get("quantity", type=float)

    if not listing_id or not quantity or quantity <= 0:
        flash("Invalid quantity requested.", "warning")
        return redirect(url_for("marketplace.index"))

    listing = db.session.get(ProduceListing, listing_id)
    if not listing or not listing.is_active:
        flash("This produce listing is no longer available.", "warning")
        return redirect(url_for("marketplace.index"))

    req_qty = Decimal(str(quantity))

    # Check against minimum order quantity
    if req_qty < listing.min_order_quantity:
        flash(f"Minimum order for {listing.name} is {listing.min_order_quantity} {listing.unit}.", "warning")
        return redirect(url_for("marketplace.product_detail", product_id=listing.id))

    # Existing cart row check
    cart_item = CartItem.query.filter_by(user_id=current_user.id, listing_id=listing.id).first()
    new_total_qty = req_qty if not cart_item else cart_item.quantity + req_qty

    if new_total_qty > listing.stock_quantity:
        flash(f"Only {listing.stock_quantity} {listing.unit} currently available in stock.", "warning")
        return redirect(url_for("marketplace.product_detail", product_id=listing.id))

    if cart_item:
        cart_item.quantity = new_total_qty
    else:
        cart_item = CartItem(user_id=current_user.id, listing_id=listing.id, quantity=req_qty)
        db.session.add(cart_item)

    db.session.commit()
    flash(f"Added {req_qty} {listing.unit} of '{listing.name}' to your shopping cart.", "success")
    return redirect(url_for("orders.cart"))


@orders_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    cart_item = db.session.get(CartItem, item_id)
    if not cart_item or cart_item.user_id != current_user.id:
        abort(404)

    action = request.form.get("action")
    if action == "increase":
        if cart_item.quantity + Decimal("1.00") <= cart_item.listing.stock_quantity:
            cart_item.quantity += Decimal("1.00")
        else:
            flash(f"Maximum stock reached for {cart_item.listing.name}.", "warning")
    elif action == "decrease":
        if cart_item.quantity > Decimal("1.00"):
            cart_item.quantity -= Decimal("1.00")
        else:
            db.session.delete(cart_item)

    db.session.commit()
    return redirect(url_for("orders.cart"))


@orders_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    cart_item = db.session.get(CartItem, item_id)
    if not cart_item or cart_item.user_id != current_user.id:
        abort(404)

    name = cart_item.listing.name
    db.session.delete(cart_item)
    db.session.commit()
    flash(f"Removed '{name}' from your cart.", "info")
    return redirect(url_for("orders.cart"))


@orders_bp.route("/checkout", methods=["GET", "POST"])
@consumer_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your shopping cart is empty. Add produce before checking out.", "warning")
        return redirect(url_for("marketplace.index"))

    subtotal = sum(item.subtotal for item in cart_items)
    delivery_fee = Decimal("50.00")
    total = subtotal + delivery_fee

    if request.method == "POST":
        recipient_name = request.form.get("recipient_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        instructions = request.form.get("instructions", "").strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")

        if not recipient_name or not phone or not address or not city or not state or not pincode:
            flash("All delivery fields are required.", "warning")
            return render_template("orders/checkout.html", cart=cart_items, subtotal=subtotal, delivery_fee=delivery_fee, total=total)

        # Atomic Transactional Stock Verification and Order Creation
        try:
            # 1. Stock validation for each produce item
            for item in cart_items:
                listing = db.session.get(ProduceListing, item.listing_id)
                if not listing or not listing.is_active or listing.stock_quantity < item.quantity:
                    db.session.rollback()
                    flash(f"Insufficient stock for '{listing.name if listing else 'Produce'}'. Please review your cart.", "danger")
                    return redirect(url_for("orders.cart"))

            # 2. Server-side verified financial totals
            verified_subtotal = sum(item.listing.price_per_unit * item.quantity for item in cart_items)
            verified_total = verified_subtotal + delivery_fee

            # 3. Create Order
            order_number = f"AGC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            order = Order(
                order_number=order_number,
                consumer_id=current_user.id,
                total_amount=verified_total,
                delivery_fee=delivery_fee,
                status="Pending",
                payment_method=payment_method,
            )
            db.session.add(order)
            db.session.flush()

            # 4. Create DeliveryDetail
            delivery = DeliveryDetail(
                order_id=order.id,
                recipient_name=recipient_name,
                phone=phone,
                address_line=address,
                city=city,
                state=state,
                pincode=pincode,
                delivery_instructions=instructions,
            )
            db.session.add(delivery)

            # 5. Create OrderItem historical snapshots & safe stock decrement
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    listing_id=item.listing_id,
                    farmer_id=item.listing.farmer_id,
                    produce_name=item.listing.name,
                    unit_price=item.listing.price_per_unit,
                    unit=item.listing.unit,
                    quantity=item.quantity,
                    subtotal=item.listing.price_per_unit * item.quantity,
                )
                db.session.add(order_item)

                # Atomically decrement listing stock
                item.listing.stock_quantity -= item.quantity

            # 6. Clear persistent cart
            for item in cart_items:
                db.session.delete(item)

            db.session.commit()
            flash(f"Order #{order.order_number} confirmed! Cash on Delivery order recorded.", "success")
            return redirect(url_for("orders.order_detail", order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred during checkout processing. Your cart remains saved.", "danger")
            return redirect(url_for("orders.cart"))

    return render_template("orders/checkout.html", cart=cart_items, subtotal=subtotal, delivery_fee=delivery_fee, total=total)


@orders_bp.route("/consumer/dashboard")
@consumer_required
def consumer_dashboard():
    orders = Order.query.filter_by(consumer_id=current_user.id).order_by(Order.created_at.desc()).all()
    active_count = sum(1 for o in orders if o.status in ("Pending", "Confirmed", "Shipped"))
    completed_count = sum(1 for o in orders if o.status == "Delivered")
    total_spent = sum(o.total_amount for o in orders if o.status != "Cancelled")

    stats = {
        "active_orders": active_count,
        "completed_orders": completed_count,
        "total_spent": total_spent,
    }
    return render_template("orders/consumer_dashboard.html", stats=stats, recent_orders=orders[:5])


@orders_bp.route("/history")
@consumer_required
def order_history():
    orders = Order.query.filter_by(consumer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders/order_history.html", orders=orders)


@orders_bp.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Authorization Check:
    # Allowed if the current user is the consumer who placed it,
    # OR if the user is a farmer who fulfills an item in this order.
    is_consumer_owner = (order.consumer_id == current_user.id)
    is_fulfilling_farmer = (
        current_user.is_farmer and current_user.farmer_profile and
        any(item.farmer_id == current_user.farmer_profile.id for item in order.items)
    )

    if not is_consumer_owner and not is_fulfilling_farmer:
        abort(403)

    return render_template("orders/order_detail.html", order=order)


@orders_bp.route("/farmer/orders", methods=["GET", "POST"])
@farmer_required
def farmer_orders():
    profile = current_user.farmer_profile
    if not profile:
        abort(403)

    if request.method == "POST":
        order_id = request.form.get("order_id", type=int)
        new_status = request.form.get("status")

        order = db.session.get(Order, order_id)
        if not order:
            abort(404)

        # Verify farmer fulfills items in this order
        if not any(item.farmer_id == profile.id for item in order.items):
            abort(403)

        allowed_statuses = {"Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"}
        if new_status in allowed_statuses:
            order.status = new_status
            db.session.commit()
            flash(f"Order #{order.order_number} status updated to '{new_status}'.", "success")

        return redirect(url_for("orders.farmer_orders"))

    # Query distinct orders containing produce from this farmer
    orders = (
        Order.query.join(Order.items)
        .filter(OrderItem.farmer_id == profile.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders/farmer_orders.html", orders=orders)
