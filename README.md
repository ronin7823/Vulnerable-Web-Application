# Flask Template

A Python/Flask web application with user authentication and a notes feature, backed by SQLite (swappable to PostgreSQL).

## Stack
- **Language**: Python 3.12
- **Framework**: Flask 3 + Flask-Login + Flask-SQLAlchemy
- **Database**: SQLite (default) — PostgreSQL optional
- **Port**: 80

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

Open [http://localhost](http://localhost), register an account, and start adding pastes.

## File Structure

```
flask/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py       # App factory, registers blueprints
    ├── models.py         # SQLAlchemy models (User, Note)
    ├── routes.py         # URL handlers split into blueprints
    └── templates/
        ├── base.html
        ├── index.html
        ├── login.html
        ├── register.html
        └── note_form.html
```

## Extending the App

### Adding a new page / feature

1. Add a route in `app/routes.py` (or create a new Blueprint file and register it in `app/__init__.py`)
2. Create a template in `app/templates/`
3. Add a model in `app/models.py` if you need a new database table
4. Run `docker compose up --build` — SQLAlchemy will auto-create new tables

### Adding a new Python package

1. Add the package to `requirements.txt`
2. Rebuild: `docker compose up --build`

### Using raw SQL queries (bypassing the ORM)

By default the app uses SQLAlchemy ORM methods (`User.query.filter_by(...)`) which automatically parameterize queries. If you want to write raw SQL — for example, to build a search feature or to explore what happens when input is interpolated directly — you can drop down to the underlying connection:

```python
from . import db

# Safe — parameterized, input never touches the SQL string directly
results = db.session.execute(
    "SELECT * FROM note WHERE title = :title",
    {"title": search_term}
).fetchall()

# Unsafe — string interpolation, vulnerable to SQL injection
# Only do this intentionally, and document it in your disclosure doc
results = db.session.execute(
    f"SELECT * FROM note WHERE title = '{search_term}'"
).fetchall()
```

To add a search route using raw SQL, add this to `app/routes.py`:

```python
@main.route("/search")
def search():
    q = request.args.get("q", "")
    # TODO: vulnerable — input handling
    results = db.session.execute(
        f"SELECT notes.*, users.username FROM notes "
        f"JOIN users ON notes.user_id = users.id "
        f"WHERE notes.title LIKE '%{q}%'"
    ).fetchall()
    return render_template("search.html", results=results, query=q)
```

### Switching to PostgreSQL

1. Uncomment the `db` service in `docker-compose.yml`
2. Change `DATABASE_URL` in your `.env` to:
   ```
   DATABASE_URL=postgresql://appuser:apppass@db:5432/appdb
   ```
3. Uncomment `psycopg2-binary` in `requirements.txt`
4. Rebuild: `docker compose up --build`

### Adding Redis (for sessions or caching)

Add to `docker-compose.yml`:
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```
Then add `Flask-Session` and `redis` to `requirements.txt` and configure `SESSION_TYPE = "redis"` in your app config.

### Accessing the database directly

```bash
# SQLite
docker compose exec app python -c "from app import db; from app.models import User; print(User.query.all())"

# Or open a shell and use sqlite3:
docker compose exec app bash
sqlite3 /app/data/app.db
```

### Enabling live code reload

The `app/` directory is mounted as a volume, so edits to Python files take effect immediately when `FLASK_ENV=development` (already set in `docker-compose.yml`). No rebuild needed for code changes — only for changes to `requirements.txt` or `Dockerfile`.

## Flags & Autograding

The template includes an autograder that helps you (and the instructor) verify your vulnerabilities actually work. Each vulnerability has a **flag** — a secret string stored as an environment variable that is revealed when the vulnerability is exploited.

### How it works

1. The template includes a working example: the `/debug` route in `app/routes.py` exposes `FLAG_EXAMPLE` without authentication
2. The example solve script (`solves/vuln1.sh`) curls `/debug` and extracts the flag
3. The autograder runs your solve scripts and checks the output against `solves/flags.txt`

### Adding your own flags

1. Add `FLAG_1`, `FLAG_2`, etc. to the `environment` section of `docker-compose.yml`
2. Write vulnerable code that reads the flag with `os.environ.get("FLAG_1")` and exposes it through the vulnerability
3. Write a solve script (`solves/vuln1.sh`, `solves/vuln2.py`, etc.) that exploits the vulnerability and prints the flag
4. List the expected flags in `solves/flags.txt`

**Delete the example `/debug` route and replace it with your own vulnerabilities before submitting.**

See [`solves/README.md`](../solves/README.md) for full documentation and examples.

## Official Documentation

- [Flask docs](https://flask.palletsprojects.com/en/3.0.x/)
- [Flask-Login docs](https://flask-login.readthedocs.io/en/latest/)
- [Flask-SQLAlchemy docs](https://flask-sqlalchemy.readthedocs.io/en/stable/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Jinja2 templating](https://jinja.palletsprojects.com/en/3.1.x/templates/)
- [Python 3 docs](https://docs.python.org/3/)
- [Werkzeug security utilities](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#module-werkzeug.security)

## Vulnerability Building Resources

Use these to learn how to intentionally introduce (and later fix) common web vulnerabilities for the midterm:

**General**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — the canonical list of web vulnerabilities
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — detailed testing methodology
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — free, hands-on labs for SQLi, XSS, CSRF, IDOR, and more

**CTF / Challenge Building**
- [CTFtime.org](https://ctftime.org/) — see real CTF challenges for inspiration
- [PicoCTF problems](https://picoctf.org/problems) — beginner-friendly web exploitation challenges
- [OWASP WebGoat](https://github.com/WebGoat/WebGoat) — deliberately insecure app you can reference
- [DVWA (Damn Vulnerable Web Application)](https://github.com/digininja/DVWA) — vulnerable PHP app showing how vulnerabilities are coded

**Specific Vulnerability Types**
- [SQL Injection (OWASP)](https://owasp.org/www-community/attacks/SQL_Injection)
- [XSS (OWASP)](https://owasp.org/www-community/attacks/xss/)
- [CSRF (OWASP)](https://owasp.org/www-community/attacks/csrf)
- [Broken Access Control (OWASP)](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [Insecure Direct Object Reference](https://owasp.org/www-community/attacks/Insecure_Direct_Object_Reference)

## Midterm Tips

- All routes are in `app/routes.py` — this is the best place to add new features
- The `User` and `Note` models in `app/models.py` show how to define tables; add more models the same way
- Think about what happens when user input from forms reaches the database and returns to the page
- The `SECRET_KEY` setting controls session security — consider what happens if it's weak or leaked
