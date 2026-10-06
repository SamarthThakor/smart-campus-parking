# Smart Campus Parking & Schedule Assistant
CS 690, Milestone 2 · Samarth Thakor and Nirmal Naik

Working Flask starter for parking recommendations based on the next class.
All seeded data and accounts are fictional.

## Implemented scope
- Session login/logout, hashed passwords and CSRF protection.
- Student browser dashboard with next class, recommendation and walking time.
- Schedule CRUD, registration and permit selection through JSON APIs.
- Administrator browser dashboard for space counts and lot closures.
- Administrator API for accepted-permit rules.
- Automated behavior tests, local source-change watcher and GitHub Actions configuration.

SQLite is the verified local database. MySQL remains the Milestone 1 deployment
target. SQLAlchemy and a MySQL driver are included, but MySQL integration and
AWS deployment have not been executed. The student UI shows seeded schedules;
schedule editing and registration APIs do not yet have complete browser forms.

## Prerequisites and cloning
Use Python 3.12 (verified locally with 3.12.14), a browser, and Git for cloning.
Internet access is needed for initial dependency installation.
Extract this package and open a terminal in the folder containing README.md.
To clone the private repository after signing in to GitHub:
    git clone https://github.com/SamarthThakor/smart-campus-parking.git
    cd smart-campus-parking

## Windows quickstart (PowerShell)
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements-dev.txt
    Copy-Item .env.example .env
    .venv\Scripts\python -m flask --app app:create_app init-db
    .venv\Scripts\python -m flask --app app:create_app seed-demo
    .venv\Scripts\python -m flask --app app:create_app run

Open http://127.0.0.1:5000. The default database is instance/parking.db.
init-db creates missing tables; it does not migrate existing schemas.
seed-demo refuses to run when users already exist, preserving existing records.
On macOS/Linux replace .venv\Scripts\python with .venv/bin/python and use
cp .env.example .env.

## Demonstration accounts
Student: alex@example.test
Administrator: jordan@example.test
Password for both: DemoParking123!

These public fictional credentials are for local demonstrations only.
Seeded schedules include a 10:00 class every day, including weekends, so the
example works on any run date. Coordinates and walking times are illustrative.

## Reproduce the core demonstration
1. Sign in as Alex. Lot B is recommended: 18 spaces, 5-minute walk.
2. Sign out; sign in as Jordan. Set Lot B to closed and click Save.
3. Sign out; sign in as Alex. Lot A is now recommended: 10 spaces, 8-minute walk.
4. Restore Lot B to open as Jordan to reset the demonstration.

Lot C starts closed; Staff Lot does not accept student permits.
Counts are reported estimates, not reservations.
A repeatable HTTP demonstration with captured JSON responses is available:
    .venv\Scripts\python scripts/capture_demo.py
The server must be running first. It temporarily closes Lot B and restores it.

## Automated verification
    .venv\Scripts\python scripts/check.py
    .venv\Scripts\python scripts/check.py --watch

Checks compile Python modules and run pytest. Failures return nonzero exit codes.
Watch mode reruns checks when application, test or dependency files change.
Press Ctrl+C to stop it. Tests use disposable temporary SQLite databases.
They never write to the demonstration database.

.github/workflows/ci.yml runs the same checks on pushes and pull requests.
Hosted workflow results are available on the repository Actions tab.

## MySQL option (not yet integration-tested)
Create an empty MySQL 8 database and a dedicated application user.
Set DATABASE_URL in .env, URL-encoding special password characters:
    mysql+pymysql://parking_user:ENCODED_PASSWORD@127.0.0.1/campus_parking

Run init-db and seed-demo. docs/schema_mysql.sql is generated from the same
SQLAlchemy metadata for review. Compiling SQL is not a MySQL integration test.
Introduce versioned migrations before changing an existing schema later.

## Configuration and deployment
DATABASE_URL defaults to the local SQLite file.
CAMPUS_TIMEZONE defaults to America/New_York.
SECRET_KEY should be set to a long random value before shared use.
Without it, local sessions use a random per-process key and reset on restart.
APP_HTTPS=1 enables Secure cookies for an HTTPS deployment.
.env, databases and virtual environments are excluded from Git.

Production WSGI serving, HTTPS, rate limiting, password reset, deployment secrets,
backups and optional maps are future deployment/product work.

## API conventions
Fetch GET /api/auth/csrf and retain the cookie. Send X-CSRF-Token on every
changing request, including login. Login returns a rotated csrf_token.
Use JSON bodies. Class operations check record ownership; admin routes check roles.

POST /api/auth/login:
    {"email":"alex@example.test","password":"DemoParking123!"}
POST /api/classes:
    {"title":"Databases","weekday":2,"start_time":"12:00",
     "end_time":"13:00","building_id":1}
PATCH /api/admin/lots/2:
    {"status":"closed"}

Codes: 200 success, 201 created, 204 no content, 400 invalid data,
401 missing session or bad login, 403 role/CSRF failure, 404 missing or not-owned
record, 409 duplicate email, 500 database error, 503 health-check database failure.

## Team workflow
Use main for reviewed work and feature/name or fix/name branches.
Use focused commits with feat:, fix:, test: or docs: prefixes.
Each pull request states the change and test results; the other member reviews.
Require passing checks and one review through repository settings when available.
These rules are policies until the remote repository is configured.

Samarth leads frontend and coordination; Nirmal leads backend, data, QA and cloud.
Both maintain interfaces, test scenarios and review documentation.

## Repository access
Repository: https://github.com/SamarthThakor/smart-campus-parking
This repository is private. The owner must grant the instructor and teammate
access before they can clone it or view the submission. Check the Actions tab
for hosted verification results.

## Files
app/                  Factory, models, services, routes, templates and static assets
tests/                Automated behavior tests
scripts/check.py      Build/test automation and watch mode
scripts/capture_demo.py  Live HTTP demonstration
.github/workflows/    Hosted CI configuration
docs/                 Schema and verification evidence
requirements*.txt     Pinned packages
.env.example          Configuration template

## References
Course Lecture 3: Features, Scenarios, and Stories.
Course Lecture 4: Software Architecture.
Flask testing: https://flask.palletsprojects.com/en/stable/testing/
SQLAlchemy constraints: https://docs.sqlalchemy.org/en/20/core/constraints.html
GitHub Actions: https://docs.github.com/en/actions/get-started/quickstart

