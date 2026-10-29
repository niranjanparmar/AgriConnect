from flask import render_template, request, redirect, url_for, flash
from app.auth import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "consumer")
    if request.method == "POST":
        flash("Logged in successfully (Demo Authentication).", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/login.html", role=role)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    role = request.args.get("role", "farmer")
    if request.method == "POST":
        flash("Registration submitted successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", role=role)


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        flash("Profile information updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    # Demo user profile data for Phase 3 UI evaluation
    user = {
        "full_name": "Ramesh Patel",
        "email": "ramesh.patel@agriconnect.local",
        "phone": "+91 98765 43210",
        "role": "Farmer",
        "farm_name": "Patel Organic Orchards",
        "state": "Gujarat",
        "district": "Rajkot",
        "address": "Survey No 42, Gondal Road, Near Market Yard",
        "pincode": "360004",
        "joined_date": "January 2026",
    }
    return render_template("auth/profile.html", user=user)


@auth_bp.route("/logout")
def logout():
    flash("You have been logged out securely.", "info")
    return redirect(url_for("main.index"))
