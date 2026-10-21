# Milestone 3: Minimum Viable Product

**Smart Campus Parking**  
CS 690 - Samarth Thakor and Nirmal Naik  
Class demonstration: October 22, 2026 | Submission due: October 23, 2026

[Setup and running instructions](#run-locally) | [Milestone 2 archive](README_Milestone2.md)

## What changed since Milestone 2

The project name changed from **Smart Campus Parking & Schedule Assistant** to
**Smart Campus Parking**. Class schedules remain part of the parking workflow.

| Area | Milestone 2 | Milestone 3 |
|---|---|---|
| Student interface | Dashboard with seeded schedules; registration, permit and schedule APIs | Browser forms for registration, permit selection, and class creation, editing and deletion |
| Recommendations | Eligible lots ranked using stored walking estimates | Accepted permit names and a clear provisional notice for future-day recommendations |
| Data storage | Persistent local SQLite; initial table creation | Automatic versioned Alembic migrations and restart-persistence checks |
| Administrator changes | Save reported spaces and lot closures | Lot updates and audit records committed together; status-only changes preserve the space-count timestamp |
| Quality checks | 28 backend tests and a GitHub Actions workflow | 42 unit/integration tests, coverage enforcement and a real browser workflow in pull-request CI |
| Evidence | Architecture, API contracts and starter verification | Working workflow screenshots, database checks, migration logs, test reports and demonstration plan |

## Completed end-to-end workflow

1. A student creates an account and saves a Student permit.
2. The student adds a class at Library Building through the browser.
3. Flask validates and saves the class to the persistent SQLite database.
4. The dashboard reads the saved schedule and recommends Lot B.
5. After restarting the server and signing in again, the saved data remains.
6. An administrator closes Lot B and saves the change.
7. The student refreshes parking and receives Lot A instead.

The browser checks also exercise invalid class-time rejection, editing, deletion and
a mobile-width layout. Sample accounts, buildings and lots are fictional; saved
changes are real database transactions.

## Database work

- `0001_initial` creates the seven core tables with their keys and constraints.
- `0002_lot_audit` adds administrator update history without replacing existing records.
- Startup applies pending migrations before requests are served.
- Tests verify upgrades from a populated revision 0001 database and persistence across restart.
- Old unversioned MS2 databases are preserved and rejected with a clear message.
  Use a separate database for the MVP; automatic import of legacy files is not implemented.

SQLite is the verified MVP database. MySQL/RDS integration and AWS hosting remain future work.

## Verification results

Recorded local verification on October 20, 2026:

- **42 tests passed**, with zero failures and zero errors.
- **95.17% statement coverage** (315 of 331 statements); the minimum enforced by CI is 85%.
- **14 browser workflow checks passed**, including server restart and changed recommendations.
- [Pull-request run #3](https://github.com/SamarthThakor/smart-campus-parking/actions/runs/39516238331)
  passed for implementation commit `c5e856b`.
- [The report-and-evidence commit's CI run](https://github.com/SamarthThakor/smart-campus-parking/actions/runs/39619494282)
  also passed for `c6fdca0`.

These are recorded results for those commits, not a claim that every later commit has
already passed. The workflow runs backend and browser checks on pushes and pull requests.

## Report and supporting evidence

- [Milestone 3 PDF](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/CS690_Milestone3_Minimum_Viable_Product.pdf)
- [Demo script and feedback record](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/DEMO_AND_FEEDBACK.md)
- [Test and coverage summary](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/test-summary.json)
- [Browser workflow results](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/result.json)
- [Startup and migration log](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/startup.log)
- [GitHub verification record](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/github-ci.json)
- [Saved student parking plan](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/student-plan.png)
- [Administrator lot closure](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/admin-lot.png)
- [Updated student recommendation](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/docs/ms3-evidence/updated-plan.png)

## Remaining milestone work

Actual feedback from the October 22 classroom demonstration is pending.
After the demonstration, record the instructor's and peers' comments in the
feedback record and update Section 4 of the PDF before the October 23 submission.

## Priorities after the demonstration

1. Resolve any failure observed in the core workflow.
2. Improve forms and navigation based on actual feedback.
3. Verify MySQL migrations and an AWS deployment path.
4. Consider the optional map after reliability and usability work.

These priorities are preliminary planning proposals, not feedback already received.

## Application setup and usage

The Milestone 3 code is on [feature/milestone-3-mvp](https://github.com/SamarthThakor/smart-campus-parking/tree/feature/milestone-3-mvp) until pull request #1 is merged. Download that branch or use the Milestone 3 ZIP before following these instructions.

## Run locally

Requires Python 3.12. Clone this public repository or extract the supplied ZIP.
Open a terminal in the inner `smart-campus-parking` folder containing `requirements.txt`
and README_Milestone3.md before running the commands below.

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
