from urllib.parse import urlsplit
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm, ProfileUpdateForm
from app.extensions import db
from app.models.user import User, FarmerProfile


def is_safe_url(target):
    """Ensure redirect URL is local to prevent open-redirect vulnerabilities."""
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_farmer:
            return redirect(url_for("marketplace.farmer_dashboard"))
        return redirect(url_for("orders.consumer_dashboard"))

    role = request.args.get("role", "consumer")
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("This account has been deactivated. Please contact support.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.full_name}! Successfully logged in.", "success")

            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            if user.is_farmer:
                return redirect(url_for("marketplace.farmer_dashboard"))
            return redirect(url_for("marketplace.index"))

        flash("Invalid email address or password. Please verify your credentials.", "danger")

    return render_template("auth/login.html", form=form, role=role)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    role = request.args.get("role", "farmer")
    form = RegistrationForm()

    if request.method == "GET" and role in ("farmer", "consumer"):
        form.role.data = role

    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data.strip().lower(),
                full_name=form.full_name.data.strip(),
                phone=form.phone.data.strip(),
                role=form.role.data,
                is_active_account=True,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()

            if user.is_farmer:
                profile = FarmerProfile(
                    user_id=user.id,
                    farm_name=form.farm_name.data.strip() if form.farm_name.data else f"{user.full_name}'s Farm",
                    farm_address=form.address.data.strip() if form.address.data else "",
                    district=form.district.data.strip(),
                    state=form.state.data,
                    pincode=form.pincode.data.strip() if form.pincode.data else "",
                    is_verified=False,
                    bio="Registered agricultural producer on AgriConnect.",
                )
                db.session.add(profile)

            db.session.commit()
            flash("Account registered successfully! You can now log in with your credentials.", "success")
            return redirect(url_for("auth.login", role=user.role))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during account registration. Please try again.", "danger")

    return render_template("auth/register.html", form=form, role=role)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileUpdateForm()

    if request.method == "GET":
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone or ""
        if current_user.is_farmer and current_user.farmer_profile:
            form.farm_name.data = current_user.farmer_profile.farm_name or ""
            form.address.data = current_user.farmer_profile.farm_address or ""
            form.district.data = current_user.farmer_profile.district or ""
            form.state.data = current_user.farmer_profile.state or ""
            form.pincode.data = current_user.farmer_profile.pincode or ""
        else:
            form.district.data = "Rajkot"
            form.state.data = "Gujarat"

    if form.validate_on_submit():
        # Verify password if user attempts to change it
        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash("Current password must be provided and correct to update your password.", "danger")
                return render_template("auth/profile.html", form=form, user=current_user)
            current_user.set_password(form.new_password.data)

        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip()

        if current_user.is_farmer:
            if not current_user.farmer_profile:
                current_user.farmer_profile = FarmerProfile(user_id=current_user.id)
            current_user.farmer_profile.farm_name = form.farm_name.data.strip() if form.farm_name.data else ""
            current_user.farmer_profile.farm_address = form.address.data.strip() if form.address.data else ""
            current_user.farmer_profile.district = form.district.data.strip()
            current_user.farmer_profile.state = form.state.data.strip()
            current_user.farmer_profile.pincode = form.pincode.data.strip() if form.pincode.data else ""

        db.session.commit()
        flash("Profile information updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, user=current_user)
