# Alpha deployment checklist

Deployment is not complete until the live checks below pass. This repository
contains a Render Blueprint, not evidence that a service has already been created.

## Prepared configuration

`render.yaml` selects a Python web service, Gunicorn 27, one worker/four threads,
and a 1 GiB disk mounted at /var/data. SQLite uses /var/data/parking.db. The
start command applies migrations through init-catalog, initializes fictional
locations without public demo accounts, and starts the application. A subsequent
start preserves catalog changes. A paid service and disk require cost approval.
Render free instances do not preserve SQLite files across restarts/redeploys.

The Blueprint derives TRUSTED_HOSTS from Render's own external hostname. For
other hosts, set it to the exact service hostname (no scheme/path). Set APP_ENV to
production, APP_HTTPS to 1, and use a generated persistent secret of at least 32
characters. Do not copy a local .env or database into the repository/deployment.
The Blueprint generates the secret without publishing it. Automatic deployment
is off so an unverified push does not change the live release.

## Operator steps after connecting the hosting account

1. Confirm service/disk cost, account and region before provisioning.
2. Deploy the verified main commit; confirm the generated host configuration.
3. In the private service console run `python -m flask --app app:create_app create-admin`.
   Enter a unique administrator email and password at the prompts. Never put the
   password in a shell argument or public documentation.
4. Check HTTPS /api/health, secure cookie flags, HSTS, CSP and a forbidden host.
5. Register a disposable student, save a permit/class and confirm recommendations.
6. Restart the service; verify the account/class persist. Close a lot as admin,
   refresh as student, and confirm the change and audit history.
7. Verify export, session logout, account deletion and expired-session behavior.
8. Record the URL, deployed commit, time and results in release evidence. Remove
   disposable accounts. Do not describe a local browser run as a cloud test.

## Backup and recovery

Before migration, stop writes and take a SQLite-consistent backup using SQLite's
backup interface (or copy only with the process stopped). Restrict its access.
Keep one application instance while startup performs migrations. A failure must
stop deployment; inspect logs without publishing secrets. Restore a validated
backup with its compatible application version if rollback is necessary; do not
blindly run migration downgrades against live records. Confirm provider backup
retention and deletion behavior before accepting real personal data.

References: https://render.com/docs/deploy-flask, https://render.com/docs/disks,
https://render.com/docs/free.
