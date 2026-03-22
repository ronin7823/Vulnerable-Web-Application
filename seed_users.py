from app import create_app, db
from app.models import User, Paste, Comment
from werkzeug.security import generate_password_hash

app = create_app()

# ----------------------------------------------------------------
# ADMIN PASSWORD LOGIC (for CTF organizer eyes only):
#   Pet name:   shadow
#   Year:       2019
#   Password:   shadow2019
#
# Students must read Joe's and Admin's posts to figure this out,
# then build a wordlist and use Hydra to spray the login.
# ----------------------------------------------------------------

USERS = [
    ("admin", "shadow2019"),   # FLAG 3 — found via OSINT + password spraying
    ("elon",  "password123"),  # FLAG 1 — found via SQL injection bypass
    ("joe",   "xK9#mPqW2!"),   # Regular user, no flag
]

# Blog posts that hint toward admin's password
# Joe mentions admin's dog "Shadow" casually
# Admin mentions the year 2019 in his own post
POSTS = [
    {
        "username": "joe",
        "title": "Welcome to CyberBlog — Introducing the Team",
        "language": "text",
        "body": """Hey everyone! Joe here. Excited to finally have a place where our security 
research community can share ideas and findings.

Big shoutout to our admin for setting this whole platform up. 
We were hanging out last weekend and his dog Shadow kept running 
around the yard while we were trying to set up the server lol. 
That dog has so much energy, hard to believe admin has had him 
for a few years already.

Anyway — welcome to the grid. Stay curious, stay ethical.

— joe""",
        "comments": [
            ("elon", "Haha Shadow is the real admin of this server 😂"),
            ("admin", "Shadow says thanks for the shoutout lol. Glad to have everyone here!"),
        ]
    },
    {
        "username": "admin",
        "title": "Platform Update + A Bit About Me",
        "language": "text",
        "body": """Hey all — admin here with a quick update on the platform.

First, a little about myself since some of you asked. I've been 
in the cybersecurity space for about 6 years now. Got really into 
it after a career change I made back in 2019 — same year I adopted 
my dog, actually. That year changed everything for me personally 
and professionally.

I tend to use personal milestones as memory anchors. Dates, names 
of things I care about — makes it easier to remember stuff that 
matters. Anyway that's probably too much about me lol.

Platform news: the blog is now open to all registered users. 
Post your research, tools, writeups — anything security related.

Stay safe out there.

— admin""",
        "comments": [
            ("joe", "2019 was a big year for a lot of us! Great to know more about you admin."),
            ("elon", "What breed is the dog? Asking for research purposes 😅"),
            ("admin", "Haha he's a black lab mix. Named him Shadow because he follows me everywhere."),
        ]
    },
    {
        "username": "elon",
        "title": "SQL Injection — Still the #1 Web Vulnerability",
        "language": "text",
        "body": """Let's talk about SQL injection. Despite being decades old, SQLi 
remains one of the most common and dangerous web vulnerabilities.

The core issue: developers trust user input and paste it directly 
into database queries without sanitization.

Example of a VULNERABLE login query:
  SELECT * FROM users WHERE username = '[INPUT]'

If an attacker inputs:   ' OR '1'='1
The query becomes:
  SELECT * FROM users WHERE username = '' OR '1'='1'

Since '1'='1' is always true, the database returns ALL users 
and the attacker gets in without a password.

Always use parameterized queries or prepared statements.
Never trust raw input.

— elon""",
        "comments": [
            ("joe", "Classic. Still shocking how many production systems are vulnerable to this in 2025."),
            ("elon", "Right? Run sqlmap on any random login form and you'd be surprised..."),
        ]
    },
]

with app.app_context():
    # Create users
    for username, password in USERS:
        existing = User.query.filter_by(username=username).first()
        if existing:
            existing.password_hash = generate_password_hash(password)
            print(f"Updated user: {username}")
        else:
            user = User(
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            print(f"Created user: {username}")
    db.session.commit()

    # Create posts
    for post_data in POSTS:
        author = User.query.filter_by(username=post_data["username"]).first()
        if not author:
            print(f"User {post_data['username']} not found, skipping post")
            continue

        # Check if post already exists
        existing_post = Paste.query.filter_by(title=post_data["title"]).first()
        if existing_post:
            print(f"Post already exists: {post_data['title']}")
            continue

        paste = Paste(
            title=post_data["title"],
            body=post_data["body"],
            language=post_data["language"],
            user_id=author.id
        )
        db.session.add(paste)
        db.session.commit()
        print(f"Created post: {post_data['title']}")

        # Add comments
        for commenter_username, comment_body in post_data.get("comments", []):
            commenter = User.query.filter_by(username=commenter_username).first()
            if commenter:
                comment = Comment(
                    body=comment_body,
                    paste_id=paste.id,
                    user_id=commenter.id
                )
                db.session.add(comment)
        db.session.commit()
        print(f"  Added comments to: {post_data['title']}")

    print("\nDone! Summary:")
    print(f"  Users:  {User.query.count()}")
    print(f"  Posts:  {Paste.query.count()}")
    print(f"  Comments: {Comment.query.count()}")
