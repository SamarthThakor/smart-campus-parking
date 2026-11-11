# Alpha security and privacy

## Implemented defenses

- Werkzeug password hashing; no plaintext credential column. Registration cannot
  select an administrator role. Private `create-admin` CLI prompts for a hidden,
  confirmed password and will not promote an existing user.
- Random session tokens stored only in an HttpOnly signed browser cookie; the
  database stores SHA-256 digests. Server-side expiry is absolute at one hour.
  Login rotates the browser session; logout deletes its server record, so replay
  of the signed-out cookie fails. Account deletion revokes every associated session.
- Central role checks and owner filters for class reads, edits and deletion.
  Exports always derive the owner from the session. Foreign user IDs in class
  input are rejected. Students cannot read administrator history or update lots.
- CSRF validation on every modifying API request, including login/registration.
  Authentication and password-confirmed deletion share persistent 15-minute
  fixed-window counters: eight attempts per account and forty per source address.
  Counters include successes and survive restarts. Atomic updates are tested
  under concurrent requests. Retry-After accompanies HTTP 429.
- HMAC identifiers keep raw attempted emails and IP addresses out of rate-limit
  storage. Expired counters and sessions are removed on authentication activity.
- Input type, length, range and reference validation; a 16 KiB request limit;
  parameterized SQLAlchemy statements; safe DOM textContent for user text.
- A same-origin CSP blocks inline scripts and framing; nosniff, no-referrer and
  restricted browser permissions complement it. API data uses no-store caching.
- Production startup rejects missing/short persistent secrets, insecure cookies
  or absent trusted hosts. Secure, HttpOnly, SameSite=Lax cookies and HSTS are
  configured. HTTPS must actually be supplied by the hosting platform.
- Production disables demonstration credentials and the seed-demo command.
  init-catalog creates fictional parking records without accounts.
- Database-error logs contain the exception class, not SQL parameters or secrets.
- Student data export/deletion and a plain-language privacy page are implemented.

## Limits and operational responsibilities

This is an alpha, not a penetration-test certification. A vulnerability scan
only identifies known advisories at scan time. Registration still returns 409
for a registered email; throttling limits but does not eliminate enumeration.
There is no email verification, password recovery or MFA yet. A stolen live
cookie remains usable until expiry or revocation. Temporary account throttling
can be abused to impede a user; monitor it before a broad launch.

Forwarding headers are not trusted. Behind a proxy, the IP limit can group users
under the proxy address; the account limit remains effective. Do not add blanket
ProxyFix trust. Configure a verified trusted proxy chain before larger deployment.

SQLite is not application-encrypted. Restrict volume/console access and verify
provider encryption and backup controls. User deletion removes live records, not
already captured backups. Establish backup retention before accepting real users.
Administrator audit history is retained for the alpha. Host access logs are
outside the application's HMAC storage policy and need separate retention rules.
Never record real student schedules or university passwords in the alpha demo.

The app has no real map/geolocation, official university parking integration,
payment processing, fines, or reservations. The browser disables geolocation.
Only a single deployment instance with a persistent SQLite disk is supported;
multi-instance deployment needs a shared database and migration coordination.

## References

- Flask security: https://flask.palletsprojects.com/en/stable/web-security/
- Flask configuration: https://flask.palletsprojects.com/en/stable/config/
- Render Flask deployment: https://render.com/docs/deploy-flask
- Persistent storage: https://render.com/docs/disks
