import os
import sqlite3
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


# ---------------------------------------------------------------------------
# FLAG 1 — SQL Injection vulnerability
# ---------------------------------------------------------------------------
# HOW IT WORKS:
#   The login query is built by gluing the username string directly into
#   raw SQL — no sanitization, no parameterization.
#
# HOW TO EXPLOIT:
#   Username:  elon' OR '1'='1
#   Password:  (anything)
#
#   This turns the query into:
#   SELECT ... WHERE username = 'elon' OR '1'='1'
#   '1'='1' is always true so the DB returns elon's row
#   and the attacker logs in without knowing the real password.
#
# FLAG revealed in the welcome flash message after bypass.
# ---------------------------------------------------------------------------

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # VULNERABLE: raw SQL string built by concatenation
        db_path = "/app/data/app.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        raw_query = "SELECT id, username, password_hash FROM user WHERE username = '" + username + "'"

        try:
            cursor.execute(raw_query)
            rows = cursor.fetchall()
        except Exception:
            rows = []
        conn.close()

        # Find elon's row specifically — injection returns all rows
        matched_row = None
        for row in rows:
            if row[1] == "elon":
                matched_row = row
                break
        if matched_row is None and rows:
            matched_row = rows[0]

        if matched_row:
            user_id, user_name, password_hash = matched_row
            injected = "' OR '" in username or "' or '" in username
            if check_password_hash(password_hash, password) or injected:
                user = User.query.get(user_id)
                if user:
                    login_user(user)
                    if user.username == "elon" and injected:
                        flash("Welcome elon! FLAG{SQLi_byp4ss_m4st3r}", "success")
                    else:
                        flash(f"Welcome back, {user.username}!", "success")
                    return redirect(url_for("main.index"))

        flash("Invalid username or password.", "danger")
    return render_template("login.html")


# ---------------------------------------------------------------------------
# Profile — FLAG 3 shown here when logged in as admin
# ---------------------------------------------------------------------------
# HOW TO GET FLAG 3:
#   1. Read the blog posts to find OSINT clues about admin
#   2. Notice: dog name = Shadow, year = 2019
#   3. Build a wordlist: shadow2019, Shadow2019, shadow19, etc.
#   4. Use Hydra to spray the login page with that wordlist
#   5. Login as admin with password: shadow2019
#   6. Visit /profile to see the flag
# ---------------------------------------------------------------------------

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

    # FLAG 3 — only visible when logged in as admin
    flag3_hint = None
    if current_user.username == "admin":
        flag3_hint = "FLAG{0S1NT_spr4y_pwn3d_4dm1n}"

    return render_template("profile.html", flag3_hint=flag3_hint)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))