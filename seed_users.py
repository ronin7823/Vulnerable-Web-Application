from app import create_app, db
from app.models import User, Paste, Comment, Message
from werkzeug.security import generate_password_hash

app = create_app()



# ----------------------------------------------------------------
# CTF PASSWORD LOGIC (organizer eyes only):
#
#   ELON — Flag 3 (password spraying):
#     Password: ENPM634@Spring
#     Hint trail: One blog post about Spring semester + ENPM634
#     Players spray login page targeting elon with Hydra
#
#   ADMIN, JOE — Supporting characters, no flags
#   OFFICE CHARS — Needed for Flag 6 (JWT IDOR on messages)
# ----------------------------------------------------------------

USERS = [
    ("admin",   "shadow2019"),        # Supporting character
    ("elon",    "ENPM634@Spring"),    # FLAG 3 — password spraying
    ("joe",     "pass"),              # Supporting character
    ("mscott",  "dundermifflin"),     # Needed for Flag 6 messages
    ("dwight",  "schrutefarms"),      # Needed for Flag 6 messages
    ("pam",     "teapot2005"),        # Needed for Flag 6 messages
    ("jhalpert","bigTuna"),           # Needed for Flag 6 messages
    ("creed",   "nX7$kQm2@pLz9#wR"), # Hidden user — FLAG 6 target
    ("wcs",     "quality99"),         # Needed for Flag 6 messages
]

# Blog posts that hint toward admin's password
# Joe mentions admin's dog "Shadow" casually
# Admin mentions the year 2019 in his own post
POSTS = [
    {
        "username": "elon",
        "title": "The Semester That Changed Everything",
        "language": "text",
        "body": """Looking back, I never expected a single semester to completely rewire how I think about security.

It was during *Spring* — I enrolled in a penetration testing course almost on a whim. ENPM634. I still remember the course code like it was yesterday.

That semester broke everything I thought I knew about building secure systems. Suddenly I was thinking like an attacker. Looking for cracks in things I used to trust. It was uncomfortable at first, then addictive.

I started applying what I learned everywhere — in my projects, in how I read code, even in how I set up my own accounts and credentials. Everything from that *Spring* became a reference point. A before and after.

If you are just getting into security, find your ENPM634 moment. Find the course, the book, the CTF that flips the switch. For me it was that *Spring* semester — everything came together @ that moment.

Old habits die hard, especially from *Spring* semester 😄

– elon""",
        "comments": [
            ("joe", "The way you talk about that semester man. You probably still use Spring in everything you do lol"),
            ("elon", "You never know but with some special characters 😅"),
            ("admin", "ENPM634 is genuinely one of the best courses out there. Good recommendation elon."),
            ("dwight", "Sentiment is irrelevant. What matters is whether the skills transferred. Did they? Results only."),
            ("elon", "Dwight yes the skills transferred lol. That is literally what the whole post is about"),
            ("dwight", "I needed confirmation. Thank you."),
            ("mscott", "I also had a semester that changed everything. It was the Spring I learned to make carbonara. Different field but same energy."),
            ("jhalpert", "Michael that is not the same thing at all"),
            ("mscott", "Pasta is a system Jim. You have to think like the pasta."),
        ]
    },
    {
        "username": "joe",
        "title": "Welcome to CyberBlog — Introducing the Team",
        "language": "text",
        "body": """Hey everyone! Joe here. Excited to finally have a place where our security \nresearch community can share ideas and findings.\n\nBig shoutout to our admin for setting this whole platform up. \nWe were hanging out last weekend and his dog Shadow kept running \naround the yard while we were trying to set up the server lol. \nThat dog has so much energy, hard to believe admin has had him \nfor a few years already.\n\nAnyway — welcome to the grid. Stay curious, stay ethical.\n\n— joe""",
        "comments": [
            ("elon", "Haha Shadow is the real admin of this server 😂"),
            ("admin", "Shadow says thanks for the shoutout lol. Glad to have everyone here!"),
            ("mscott", "GREAT post Joe. Very professional. I would have written it differently but this is also good."),
            ("dwight", "I have already completed a full security audit of this platform. It is mostly secure. Mostly."),
            ("pam", "So excited for this! Finally a place to share research that isn't just the Slack #general channel 😊"),
            ("jhalpert", "Looking forward to it. Also Dwight what does 'mostly' mean exactly"),
            ("dwight", "It means what it means Jim. Drop it."),
        ]
    },
    {
        "username": "admin",
        "title": "Platform Update + A Bit About Me",
        "language": "text",
        "body": """Hey all — admin here with a quick update on the platform.\n\nFirst, a little about myself since some of you asked. I've been \nin the cybersecurity space for about 6 years now. Got really into \nit after a career change I made back in 2019 — same year I adopted \nmy dog, actually. That year changed everything for me personally \nand professionally.\n\nI tend to use personal milestones as memory anchors. Dates, names \nof things I care about — makes it easier to remember stuff that \nmatters. Anyway that's probably too much about me lol.\n\nPlatform news: the blog is now open to all registered users. \nPost your research, tools, writeups — anything security related.\n\nStay safe out there.\n\n— admin""",
        "comments": [
            ("joe", "2019 was a big year for a lot of us! Great to know more about you admin."),
            ("elon", "What breed is the dog? Asking for research purposes 😅"),
            ("admin", "Haha he's a black lab mix. Named him Shadow because he follows me everywhere."),
            ("pam", "Using personal milestones as memory anchors is actually a really common technique. Also Shadow is a great name 🐶"),
            ("mscott", "I also had a life-changing year. Mine was 2007 when I invented the perfect grilled cheese. Different kind of milestone."),
            ("dwight", "Personal information shared online is a security liability. I have noted everything in this post for my threat assessment files."),
            ("jhalpert", "Dwight has threat assessment files on all of us. Mine apparently lists 'excessive smirking' as a vulnerability."),
            ("dwight", "It is not a joke Jim. Smirking is a social engineering technique and you know it."),
        ]
    },
    {
        "username": "elon",
        "title": "SQL Injection — Still the #1 Web Vulnerability",
        "language": "text",
        "body": """Let's talk about SQL injection. Despite being decades old, SQLi \nremains one of the most common and dangerous web vulnerabilities.\n\nThe core issue: developers trust user input and paste it directly \ninto database queries without sanitization.\n\nExample of a VULNERABLE login query:\n  SELECT * FROM users WHERE username = '[INPUT]'\n\nIf an attacker inputs:   ' OR '1'='1\nThe query becomes:\n  SELECT * FROM users WHERE username = '' OR '1'='1'\n\nSince '1'='1' is always true, the database returns ALL users \nand the attacker gets in without a password.\n\nAlways use parameterized queries or prepared statements.\nNever trust raw input.\n\n— elon""",
        "comments": [
            ("joe", "Classic. Still shocking how many production systems are vulnerable to this in 2025."),
            ("elon", "Right? Run sqlmap on any random login form and you'd be surprised..."),
            ("pam", "This is genuinely scary. I just checked and our old company portal definitely didn't sanitize inputs 😬"),
            ("mscott", "I put ' OR '1'='1 into the Scranton vending machine once and got a free Twix. Is that the same thing?"),
            ("dwight", "I have been using parameterized queries since 2003. I was ahead of my time. Most people are not me."),
            ("admin", "Great writeup elon. SQLi is still embarrassingly easy to find on real systems. Always sanitize your inputs people."),
            ("jhalpert", "Michael the Twix thing is not the same thing. Although honestly I'm impressed it worked."),
            ("mscott", "The machine gave me two. I think I accidentally did a union attack."),
            ("elon", "Michael that is not how any of this works but I genuinely cannot explain why that's funny to me"),
        ]
    },
    {
        "username": "joe",
        "title": "IDOR — The Vulnerability Hiding in Plain Sight",
        "language": "text",
        "body": """Let's talk about Insecure Direct Object Reference — or IDOR.\n\nIt's one of the simplest vulnerabilities to understand and one of \nthe most embarrassingly common to find in the wild.\n\nThe idea: a web app exposes an internal object ID directly in the URL:\n  /messages/1\n  /invoices/4821\n  /users/7/profile\n\nIf the app doesn't verify that YOU are allowed to access that object, \nan attacker just changes the number and reads someone else's data. \nThat's it. No fancy exploit. Just change a number in the URL.\n\nA real example: in 2015 a researcher found an IDOR in Facebook's system \nthat let anyone delete any photo by changing a single parameter. \nEarned a $12,500 bug bounty.\n\nThe fix is always the same — on every request, verify that the \nlogged-in user actually owns or has permission to access the object \nthey're asking for. Never trust the client to enforce that.\n\nNext time you're on a web app, check the URLs. You might be surprised \nwhat you find just by changing a number.\n\n— joe""",
        "comments": [
            ("elon", "Great writeup. IDOR is criminally underrated as a vuln class. Easy to find, high impact."),
            ("admin", "Solid post. Seen this in production more times than I'd like to admit. Always check your access controls."),
            ("dwight", "I have personally audited every ID on this platform. All secure. Do not attempt."),
            ("mscott", "I once changed a number in a URL and my whole Netflix disappeared. Was that IDOR??"),
            ("pam", "The Facebook example is wild. $12,500 just for changing a number in a URL. Maybe I'm in the wrong field lol"),
            ("elon", "Pam that's literally what bug bounties are. You should try it — HackerOne is a great place to start."),
            ("joe", "100% agree with elon. Lots of platforms pay well for this exact class of bug. Worth learning."),
            ("jhalpert", "So theoretically if this platform had an IDOR and I found it, someone would owe me $12,500?"),
            ("admin", "Theoretically. Good luck 😉"),
            ("dwight", "Jim do NOT attempt to hack this platform. I am watching the logs."),
            ("jhalpert", "I'm just asking questions Dwight."),
        ]
    },
    {
        "username": "wcs",
        "title": "Hello I Am A Security Professional",
        "language": "text",
        "body": """Hello. My name is William Charles Schneider and I am a cyber security \nprofessional with over 30 years of experience in the field.\n\nI have hacked many things. I cannot list them here for legal reasons.\n\nMy top security tips:\n\n1. If a website asks for your password, give them a fake one first \nand see what happens.\n2. Encryption is when you write something in a different language. \nI am fluent in four languages so I am very encrypted.\n3. The dark web is just the regular web but with the brightness turned down.\n4. If you think you've been hacked, unplug everything and move.\n\nI am available for consulting. Rates negotiable. Cash only.\n\n— William Charles Schneider, CEH, CISSP, MBA (all pending)""",
        "comments": [
            ("mscott", "This is incredibly informative. William you should write more posts!!"),
            ("pam", "...who is William Charles Schneider? We don't have anyone by that name on the platform."),
            ("dwight", "I have run a full background check on William Charles Schneider. The results are deeply concerning. Do not engage with this individual."),
            ("elon", "The dark web tip is sending me 💀"),
            ("joe", "Whoever wrote this — 'unplug everything and move' is genuinely the funniest incident response plan I've ever seen."),
            ("jhalpert", "Four languages. Very encrypted. I'm going to think about this for the rest of the week."),
            ("mscott", "I already booked a consulting session. We are meeting in a Wendy's parking lot on Thursday. Very professional setup."),
            ("admin", "I'm looking into who posted this. Stand by."),
            ("pam", "Michael please do not go to the Wendy's parking lot"),
            ("mscott", "Too late Pam. William has already confirmed. He said to bring exact change."),
        ]
    },
    {
        "username": "wcs",
        "title": "My Thoughts on Firewalls",
        "language": "text",
        "body": """A lot of people ask me about firewalls. I tell them the same thing \nevery time: a firewall is your friend, unless it isn't.\n\nI once bypassed a firewall by simply asking the IT guy to turn it off \nfor a few minutes. He said no at first. I waited. Eventually he had \nto use the bathroom. That's called social engineering.\n\nSome other things I know about cybersecurity:\n\n- Cookies are not just for eating. They are also on websites. \nI have eaten 4000 of them (both kinds).\n- A VPN stands for Very Private Network. Mine is very private. \nI will not say where it is.\n- Two-factor authentication is when you have two passwords. \nI have seventeen.\n\nIf you want to learn more, I teach a course out of my car on Thursdays. \nBring cash and do not tell anyone you are coming.\n\n— W.C. Schneider\nFounder, Schneider Cyber Solutions LLC (not registered)""",
        "comments": [
            ("mscott", "I went to the Thursday course. Learned a lot. The car was very small but the content was world class."),
            ("pam", "Admin can we PLEASE look into who is posting these?? This is the second one."),
            ("joe", "The social engineering bathroom story is either genius or a felony. Possibly both."),
            ("dwight", "I have reported this post to the authorities. All three of them."),
            ("elon", "Seventeen passwords. Seventeen. Honestly respect the commitment even if literally everything else here is wrong."),
            ("jhalpert", "The bathroom move is actually a classic tailgating attack. Whoever William is, he accidentally described a real technique."),
            ("admin", "I know who this is. It is being handled. Please stop attending the Thursday car course."),
            ("mscott", "Too late. I already referred three people. The waitlist is very long."),
            ("pam", "There is a WAITLIST??"),
            ("mscott", "Six people Pam. William Charles Schneider is in high demand."),
        ]
    },
]

# ---------------------------------------------------------------------------
# FLAG 6 — IDOR on private messages
# ---------------------------------------------------------------------------
# HOW TO EXPLOIT:
#   1. Log in as any user -> go to /inbox -> copy the JWT token from a link.
#   2. Paste into jwt.io -> decode payload -> see {"msg_id": N}.
#   3. Crack the weak signing secret with hashcat:
#      hashcat -a 0 -m 16500 <token> rockyou.txt  ->  cracks "secret123"
#   4. Go back to jwt.io -> change msg_id to 6 -> re-sign with secret123.
#   5. Visit /messages/<forged_token> -> flag fires.
# ---------------------------------------------------------------------------

MESSAGES = [
    # --- Decoy message #1 ---
    {
        "sender":    "mscott",
        "recipient": "dwight",
        "subject":   "URGENT: We Got Hacked???",
        "body": (
            "Dwight,\n\n"
            "Someone just told me that SQL injection is when hackers put needles "
            "into your database. Is that true?? I need you to check every table "
            "in the office immediately. Also check under the keyboards.\n\n"
            "I read online that we should use 'parameterized queries'. "
            "I don't know what that means but it sounds expensive. "
            "Look into it. That's a Michael Scott order.\n\n"
            "Also I tried typing ' OR '1'='1 into our blog login page to see what "
            "would happen. Nothing happened. I think we are safe.\n\n"
            "— Michael"
        ),
    },
    # --- Decoy message #2 ---
    {
        "sender":    "dwight",
        "recipient": "pam",
        "subject":   "Mandatory Password Policy — Effective Immediately",
        "body": (
            "Pam,\n\n"
            "Effective immediately, all CyberBlog passwords must meet "
            "the following Schrute Security Standards:\n\n"
            "- Minimum 17 characters\n"
            "- Must contain at least one beet-related word\n"
            "- Must not be guessable by a black bear\n"
            "- Must be changed every 9 days\n"
            "- Must not be written down anywhere except the Schrute-approved "
            "encrypted beet tin kept in the filing cabinet\n\n"
            "My current password is 49 characters long, salted, and hashed. "
            "I will not be sharing it. Not even with Michael.\n\n"
            "Especially not with Michael.\n\n"
            "— Dwight K. Schrute\n"
            "Head of Security, IT, and Beet Operations"
        ),
    },
    # --- Decoy message #3 ---
    {
        "sender":    "pam",
        "recipient": "mscott",
        "subject":   "Re: That Phishing Email",
        "body": (
            "Hi Michael,\n\n"
            "Just a heads up — the email you forwarded to the whole office titled "
            "'YOU HAVE WON A FREE PRINTER' was a phishing attempt. "
            "Please do not click the link. Please also ask Kevin to stop "
            "trying to claim the printer.\n\n"
            "The link installs a keylogger. A keylogger records everything you type "
            "including passwords. This is very bad. Please tell Kevin.\n\n"
            "Also Dwight has set up a 'Cyber Perimeter' around his desk using "
            "binder clips and string. I'm not sure what this achieves but "
            "he seems very confident about it.\n\n"
            "— Pam"
        ),
    },
    # --- Decoy message #4 ---
    {
        "sender":    "mscott",
        "recipient": "pam",
        "subject":   "My New Blog Post Idea — Need Proofreading",
        "body": (
            "Pammy,\n\n"
            "I am going to write a CyberBlog post called:\n\n"
            "'The 10 Commandments of Hacking — by Michael G. Scott'\n\n"
            "Commandment 1: Thou shalt not hack someone who is cooler than you.\n"
            "Commandment 2: Always hack with a buddy. Hacking alone is dangerous "
            "and also sad.\n"
            "Commandment 3: If you find a vulnerability, keep it. That is called "
            "a zero day and it is worth money.\n"
            "Commandment 4: Use a VPN. I don't know what that stands for but "
            "Dwight says it is important.\n\n"
            "I need you to proofread it. Also google what a buffer overflow is "
            "and send me a summary. Two sentences max, I'm very busy.\n\n"
            "— World's Best Ethical Hacker (probably), Michael"
        ),
    },
    # --- Decoy message #5 ---
    {
        "sender":    "dwight",
        "recipient": "mscott",
        "subject":   "Threat Assessment Report — CyberBlog Platform",
        "body": (
            "Michael,\n\n"
            "I have completed a full penetration test of our CyberBlog platform. "
            "My findings are classified THREAT LEVEL MIDNIGHT:\n\n"
            "- Jim Halpert has been seen reading other people's blog posts "
            "without commenting. Classic reconnaissance behavior.\n"
            "- Kevin's password is almost certainly 'cookies'. "
            "I attempted to verify this. He changed it to 'cookies2'. Worse.\n"
            "- Toby from HR attempted to post a comment. I deleted it. "
            "HR is not security-cleared for public-facing content.\n"
            "- Someone named 'William Charles Schneider' is posting on our platform. "
            "I do not know this person. I am investigating.\n\n"
            "Recommend immediate implementation of multi-factor authentication. "
            "My second factor will be a riddle that only I can answer.\n\n"
            "Bear. Beets. Buffer Overflow.\n"
            "— D. Schrute, C.I.S.S.P. (Certified Internet Safety and Schrute Person)"
        ),
    },
    # --- FLAG message #6 — admin -> creed ---
    # Body is intentionally plain. The flag ONLY appears via the IDOR
    # banner in view_message.html when show_flag fires (message_id == 6
    # and not is_my_message). Creed seeing their own inbox reveals nothing.
    {
        "sender":    "admin",
        "recipient": "creed",
        "subject":   "Platform Credentials — Confidential",
        "body": (
            "Creed,\n\n"
            "As discussed, I've provisioned your elevated access to the platform "
            "backend. This includes read access to all user posts, sessions, "
            "and the message archive. Do NOT share this with anyone.\n\n"
            "Your access token has been activated. Check your panel.\n\n"
            "And Creed — please stop posting blog articles under the name "
            "'William Charles Schneider'. We know it's you. Dwight also knows. "
            "He has filed three separate reports.\n\n"
            "— admin"
        ),
    },
]


with app.app_context():
    # ----------------------------------------------------------------
    # Create users
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # Create posts
    # ----------------------------------------------------------------
    for post_data in POSTS:
        author = User.query.filter_by(username=post_data["username"]).first()
        if not author:
            print(f"User {post_data['username']} not found, skipping post")
            continue

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

    # ----------------------------------------------------------------
    # Seed messages (IDOR flag — FLAG 6)
    # ----------------------------------------------------------------
    if Message.query.count() == 0:
        for msg_data in MESSAGES:
            sender    = User.query.filter_by(username=msg_data["sender"]).first()
            recipient = User.query.filter_by(username=msg_data["recipient"]).first()
            if sender and recipient:
                msg = Message(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    subject=msg_data["subject"],
                    body=msg_data["body"],
                )
                db.session.add(msg)
        db.session.commit()
        print(f"  Seeded {Message.query.count()} messages (FLAG 6 banner fires on /messages/<token for id=6>)")
    else:
        print(f"  Messages already seeded ({Message.query.count()} found), skipping")

    print("\nDone! Summary:")
    print(f"  Users:    {User.query.count()}")
    print(f"  Posts:    {Paste.query.count()}")
    print(f"  Comments: {Comment.query.count()}")
    print(f"  Messages: {Message.query.count()}")