# Milestone 3: Minimum Viable Product

**Smart Campus Parking**  
CS 690 - Samarth Thakor and Nirmal Naik  
Class demonstration: October 22, 2026 | Submission due: October 23, 2026

[Current setup and running instructions](https://github.com/SamarthThakor/smart-campus-parking/blob/feature/milestone-3-mvp/README.md) | [Milestone 2 archive](README_Milestone2.md)

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
