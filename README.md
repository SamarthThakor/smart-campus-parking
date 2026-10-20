# Smart Campus Parking

CS 690 - Milestone 3: Minimum Viable Product  
Samarth Thakor and Nirmal Naik

Students create an account, save a permit, manage their weekly classes, and get a
parking recommendation. Administrators change lot status and reported space counts.
The browser calls Flask JSON routes, and SQLAlchemy commits records to a persistent
SQLite database. All sample campus locations and demo accounts are fictional.

The project was previously titled **Smart Campus Parking & Schedule Assistant**.
Milestone 3 uses the shorter name **Smart Campus Parking**; class scheduling remains
part of the parking workflow. Historical milestone PDFs retain their submitted titles.

## Run locally

Requires Python 3.12. Clone this public repository or extract the supplied ZIP.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.venv\Scripts\python -m flask --app app:create_app seed-demo
.venv\Scripts\python -m flask --app app:create_app run
```

Open http://127.0.0.1:5000. On Linux/macOS use `.venv/bin/python` and `cp`.
Application startup applies Alembic migrations automatically, before serving requests.
The default database is `instance/parking.db`; it persists after browser or server restarts.
Run `seed-demo` once on an empty database. It refuses to overwrite existing users.

Local demo accounts: `alex@example.test` (student) and `jordan@example.test` (admin).
Both use `DemoParking123!`. You can also register a new student in the browser.
The signup form never creates administrators.

## Demonstrate the vertical slice

1. Create a student account, select **Student**, and save the permit.
2. Add a class at Library Building for tomorrow at 10:00-11:00, using the displayed
   campus time zone. The saved class appears in the schedule.
3. See Lot B, 18 reported spaces, a five-minute walk and the accepted permit list.
4. Restart Flask, then sign in again. The account, permit and class still exist.
5. In a separate browser session, sign in as Jordan and close Lot B. Click **Save lot**.
6. Refresh the student's parking plan. Lot A replaces Lot B, with an eight-minute walk.
7. Reopen Lot B after demonstrating. Editing/deleting a class and invalid time errors
   can also be shown from the schedule form.

Future-day recommendations are provisional. Counts are administrator reports, not
reservations or forecasts. Class and parking times display in `CAMPUS_TIMEZONE`.

## Database migrations and integrity

`app/migrations.py` runs `alembic.command.upgrade(config, "head")` at startup.
The migrations are frozen separately from current application models:

- `0001_initial`: seven related tables for users, permits, buildings, classes, lots,
  lot-permit rules and walking estimates.
- `0002_lot_audit`: adds an administrator update history table without replacing
  existing records. Each lot change and its audit entry commit in one transaction.

`alembic_version` records the current revision. A repeat startup performs no schema
changes. Tests upgrade a populated revision 0001 database and verify its records survive.
SQLite foreign-key enforcement is enabled on every application connection. Foreign
keys, unique email/permit names, composite keys, non-null columns and check constraints
protect the data; server validation checks time ranges, capacity and record ownership.

Keep any old MS2 `parking.db` as a backup. An unversioned database is deliberately
rejected rather than silently stamped or overwritten. For this MVP, start a new file
by setting a new absolute SQLite `DATABASE_URL` in `.env`. No existing user database
is deleted by the setup. Data import from unversioned MS2 files is future work.

Back up a stopped local database by copying its file. Restore the copy with the same
application version and start it to apply any newer migrations. Never run competing
migration processes; the local MVP uses a single Flask process. Production deployment
should run one migration job before starting workers.

SQLite is a real file-backed relational database, not an in-memory mock. It is sufficient
for this local MVP. MySQL/RDS and AWS remain planned deployment work and are not verified
by this milestone. The old MySQL schema export in `docs/` is historical MS2 evidence.

## Tests and continuous integration

```powershell
.venv\Scripts\python scripts/check.py
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python scripts/browser_demo.py
```

`check.py` compiles Python and runs unit/integration tests with statement coverage.
Coverage below 85% fails the check. XML/JSON coverage and JUnit reports are saved to
`artifacts/`. `--watch` reruns backend checks on source changes.

`browser_demo.py` launches an isolated live Flask server and a real browser. It tests
registration, permit selection, schedule creation/edit/deletion, restart persistence,
admin closure, changed recommendations, validation and a mobile-width layout. It saves
screenshots, startup logs and `result.json` under `artifacts/browser/`. Its database is
isolated from the user's demo database. Set `BROWSER_CHANNEL=chrome` to use installed
Chrome instead of downloaded Chromium when needed.

`.github/workflows/ci.yml` runs backend tests and the browser flow on **every push and
pull request**, then uploads evidence even if a check fails. A configured workflow is
distinct from an observed passing run; see the Milestone 3 verification record for
the actual PR run and tested commit. Branch protection is not configured by this work.

## Configuration

- `DATABASE_URL`: defaults to the local SQLite file.
- `CAMPUS_TIMEZONE`: defaults to `America/New_York`.
- `SECRET_KEY`: set a long random value for shared use; otherwise sessions reset
  when the application restarts. Database records remain saved.
- `APP_HTTPS=1`: enables Secure cookies after configuring HTTPS.

Session cookies are HttpOnly and SameSite=Lax; writes require a CSRF token. Passwords
are hashed. Student class routes enforce ownership, and lot writes require an admin.
The local development server, public demo passwords, and untested deployment settings
are not a production hosting setup. HTTPS, rate limiting, password recovery, optional
maps and MySQL deployment remain future work.

## Milestone 3 handoff

The PDF is in `docs/CS690_Milestone3_Minimum_Viable_Product.pdf`.
`docs/DEMO_AND_FEEDBACK.md` contains the live-demo script and feedback record.
The live classroom demonstration is October 22, 2026; submission is October 23.
Actual peer/instructor feedback must be added after the demonstration. No classroom
feedback is invented or represented as already received.

Samarth leads frontend and coordination; Nirmal leads backend, database, testing and
cloud planning. Both review the workflow and prepare the demonstration. Use feature
branches and pull requests, with the other team member reviewing before merge.

Repository: https://github.com/SamarthThakor/smart-campus-parking
