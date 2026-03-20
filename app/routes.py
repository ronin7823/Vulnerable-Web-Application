import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Paste, Comment

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Main routes
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    pastes = Paste.query.order_by(Paste.id.desc()).all()
    return render_template("index.html", pastes=pastes)


# EXAMPLE vulnerability — information disclosure, no auth check.
# Replace this with your own vulnerabilities and delete this route.
@main.route("/debug")
def debug():
    # TODO: vulnerable — exposes environment variable without authentication
    return os.environ.get("FLAG_EXAMPLE", "no flag set")


@main.route("/pastes/new", methods=["GET", "POST"])
@login_required
def new_paste():
    if request.method == "POST":
        title = request.form.get("title", "")
        body = request.form.get("body", "")
        language = request.form.get("language", "text")
        paste = Paste(title=title, body=body, language=language, user_id=current_user.id)
        db.session.add(paste)
        db.session.commit()
        flash("Paste created.", "success")
        return redirect(url_for("main.index"))
    return render_template("paste_form.html")


@main.route("/pastes/<int:paste_id>/comments", methods=["POST"])
@login_required
def add_comment(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    body = request.form.get("comment", "").strip()
    if not body:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("main.index"))

    comment = Comment(body=body, paste_id=paste.id, user_id=current_user.id)
    db.session.add(comment)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("main.index"))


@main.route("/pastes/<int:paste_id>/delete", methods=["POST"])
@login_required
def delete_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    db.session.delete(paste)
    db.session.commit()
    flash("Paste deleted.", "info")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.register"))
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("main.index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(current_user.password_hash, old_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("main.profile"))

        if not new_password or new_password != confirm_password:
            flash("New passwords do not match or are empty.", "danger")
            return redirect(url_for("main.profile"))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "danger")
            return redirect(url_for("main.profile"))

        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
