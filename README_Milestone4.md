# Milestone 4: Alpha Release and Software Security

Smart Campus Parking | CS 690 | Samarth Thakor and Nirmal Naik

The alpha retains the Milestone 3 parking workflow and adds student data export
and deletion, an administrator history view, persistent login throttling, and
server-revocable one-hour sessions. It separates HTTP helpers, security,
authentication, profiles, schedules, parking, and validation into focused modules.

## Run locally

Use Python 3.12 in a virtual environment, install `requirements-dev.txt`, then:

```text
python -m flask --app app:create_app seed-demo
python -m flask --app app:create_app run
```

Run `seed-demo` once on an empty local database. It never overwrites users.
The local-only demo accounts remain documented in README_Milestone3.md.
Use fictional information for the alpha. This is not an official LIU service.

## Verify

```text
python scripts/check.py
python -m playwright install chromium
python scripts/browser_demo.py
```

The first command runs backend tests with an 85% statement-coverage gate. The
second installs the browser needed by the third. Evidence is written under
`artifacts/`. The browser uses an isolated database and tests the complete
registration-to-recommendation workflow, restart persistence, administrator
changes, export, deletion, stored-XSS handling and mobile layout.

Recorded alpha evidence is in `docs/ms4-evidence/`. It is a snapshot of a tested
build, not a promise that every future revision passes.

## Technical documentation

- [API contract](docs/API_ALPHA.md)
- [Security and privacy](SECURITY.md)
- [Deployment and release checks](docs/DEPLOYMENT_ALPHA.md)

The database upgrades from `0002_lot_audit` to `0003_alpha_security` without
replacing users or schedules. Existing browser sessions must sign in again.
Unversioned legacy databases are still rejected without alteration.

## Deferred work

An interactive LIU Post map needs verified campus coordinates, permission for
map assets, and an agreed meaning of "live". Overtime penalties need approved
duration, grace-period, charge and timing rules, plus a parking-session model.
Neither is implemented or represented as official university policy. Current
counts and locations are fictional and are manually updated; no reservations,
sensor integration, official fines, or measured travel-time savings are claimed.

The alpha is merged into main (PR #2) and deployed on AWS Lightsail:
https://smartcampusparking.34-233-200-219.sslip.io

Backend and browser CI passed before merge. Nineteen live checks passed,
including trusted HTTPS, secure cookies, authorization, CSRF, student data
export/deletion and persistence across service restart. Certificate renewal
dry-run succeeded. See [AWS deployment record](docs/DEPLOYMENT_AWS.md).

The account stays on AWS Free plan and uses promotional credits only. Do not
upgrade it or authorize card charges. Private administrator creation is still
an operator handoff; live administrator operations are not yet verified.
