# AWS alpha deployment plan

Status: AWS host provisioned on 2026-11-11; application installation and HTTPS
verification are still pending. Do not describe the application as live yet.
The AWS billing console confirms a Free plan that does not charge, with
USD 100 credits and 182 days remaining when inspected. Do not upgrade this
account or authorize real-money charges. The user permits free credits only.

Host: smart-campus-parking-alpha, us-east-1a, Ubuntu 24.04, 1 GB RAM / 40 GB SSD.
Attached static IP: 34.233.200.219 (smart-campus-parking-ip).
Planned URL: https://smartcampusparking.34-233-200-219.sslip.io
SSH access is restricted to the Lightsail browser SSH client.

## Proposed service

One Ubuntu 24.04 Lightsail Linux instance with public IPv4, 1 GiB memory and
40 GiB persistent SSD storage. AWS lists this bundle at USD 7/month, billed
hourly up to the monthly bundle cost. Taxes, snapshots and excess usage may
cost extra. Confirm the account, region and final console estimate first.
Attach a static IPv4 address so restarts do not invalidate the app address.
Keep it attached; an unattached static address can incur charges.

The app uses the instance's persistent disk, Gunicorn on loopback, nginx on
ports 80/443 and a dedicated non-login system user. No public port 8000 or
database port is needed. Restrict SSH to approved administration access.
Use only fictional data during the alpha.

## HTTPS without purchasing a domain

The free sslip.io hostname embeds the attached static IP and requires no domain
purchase. Let's Encrypt provides its HTTPS certificate. The prepared installer
checks renewal every six hours and reloads nginx after renewal. It requires
approval of the CA subscriber agreement before running. Certificate issuance
and renewal must be tested on the real host; no self-signed bypass is allowed.

## Installation

After cost, public-service exposure and certificate terms are approved, create
the fresh host, attach its static IP, and allow HTTP/HTTPS. Review then run
`scripts/install_aws_alpha.sh` as root with the full verified Git commit SHA and
the actual static IPv4 address. The installer clones only the public repository,
checks out that exact commit, creates a private persistent secret on the host,
applies migrations, and seeds fictional parking catalog data without accounts.
It refuses to overwrite an existing installation.

Create an administrator from the private host console:

```sh
sudo -u parking sh -c 'set -a; . /etc/smart-campus-parking.env; set +a; cd /opt/smart-campus-parking; .venv/bin/python -m flask --app app:create_app create-admin'
```

Enter credentials at the prompts yourself. Never paste them into source, public
logs or chat. Sessions, class data and administrator changes live in
`/var/lib/smart-campus-parking/parking.db`. The app account can write that
directory; application source and system configuration remain root-owned.

## Required verification

Confirm HTTPS certificate trust, HTTP redirect, response headers, no public demo
passwords, login/registration, permit and class persistence across service
restart, administrator closure and history, student export/deletion, and
`certbot renew --dry-run`. Record the deployed commit, URL, region and results.
Test failures must be resolved before claiming the cloud requirement complete.

Take a SQLite-consistent backup before upgrades. Restrict backup access and agree
retention before storing real student data. This installer is fresh-host-only;
upgrades need a reviewed backup/migration/rollback procedure. Rate limiting
currently groups traffic behind nginx's loopback address; the per-account limit
remains active. Configure and test a narrowly trusted proxy before wider use.

## Official references

- https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html
- https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html
- https://letsencrypt.org/repository/
- https://nip.io/
- https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
