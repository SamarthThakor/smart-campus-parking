#!/usr/bin/env bash
# Fresh Ubuntu 24.04 Lightsail host only. Run after approving infrastructure
# charges and the Let's Encrypt subscriber agreement. Does not create AWS resources.
set -euo pipefail
if [[ ${EUID} -ne 0 || $# -ne 2 ]]; then
  echo 'Usage: sudo bash install_aws_alpha.sh VERIFIED_COMMIT_SHA STATIC_IPV4' >&2
  exit 2
fi
RELEASE_SHA=$1
PUBLIC_IP=$2
[[ $RELEASE_SHA =~ ^[a-f0-9]{40}$ ]] || { echo 'A full commit SHA is required.' >&2; exit 2; }
python3 -c 'import ipaddress,sys; assert ipaddress.ip_address(sys.argv[1]).version == 4' "$PUBLIC_IP"
PUBLIC_HOST="smartcampusparking.${PUBLIC_IP//./-}.sslip.io"
if [[ -e /etc/smart-campus-parking.env || -e /opt/smart-campus-parking ]]; then
  echo 'Existing installation found. Stop and use a reviewed upgrade with a backup.' >&2
  exit 2
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y python3-venv python3-pip nginx git ca-certificates
useradd --system --home /var/lib/smart-campus-parking --shell /usr/sbin/nologin parking
install -d -o parking -g parking -m 700 /var/lib/smart-campus-parking
git clone https://github.com/SamarthThakor/smart-campus-parking.git /opt/smart-campus-parking
git -C /opt/smart-campus-parking checkout --detach "$RELEASE_SHA"
python3 -m venv /opt/smart-campus-parking/.venv
/opt/smart-campus-parking/.venv/bin/pip install -r /opt/smart-campus-parking/requirements-prod.txt
ln -s /var/lib/smart-campus-parking /opt/smart-campus-parking/instance
umask 077
SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
cat > /etc/smart-campus-parking.env <<EOF
APP_ENV=production
APP_HTTPS=1
SECRET_KEY=$SECRET
DATABASE_URL=sqlite:////var/lib/smart-campus-parking/parking.db
TRUSTED_HOSTS=$PUBLIC_HOST
CAMPUS_TIMEZONE=America/New_York
EOF
unset SECRET
chown root:parking /etc/smart-campus-parking.env
chmod 640 /etc/smart-campus-parking.env
cat > /etc/systemd/system/smart-campus-parking.service <<'EOF'
[Unit]
Description=Smart Campus Parking alpha
After=network.target
[Service]
User=parking
Group=parking
WorkingDirectory=/opt/smart-campus-parking
EnvironmentFile=/etc/smart-campus-parking.env
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStartPre=/opt/smart-campus-parking/.venv/bin/python -m flask --app app:create_app init-catalog
ExecStart=/opt/smart-campus-parking/.venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 1 --threads 4 app:create_app()
Restart=on-failure
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/smart-campus-parking
[Install]
WantedBy=multi-user.target
EOF
install -d -m 755 /var/www/acme
cat > /etc/nginx/sites-available/parking <<EOF
server {
  listen 80 default_server;
  server_name $PUBLIC_HOST;
  location /.well-known/acme-challenge/ { root /var/www/acme; }
  location / { return 503; }
}
EOF
if [[ -L /etc/nginx/sites-enabled/default ]]; then unlink /etc/nginx/sites-enabled/default; fi
ln -s /etc/nginx/sites-available/parking /etc/nginx/sites-enabled/parking
nginx -t
systemctl reload nginx
python3 -m venv /opt/parking-certbot
/opt/parking-certbot/bin/pip install 'certbot>=5.4,<7'
# This command accepts the CA agreement; obtain the user's approval before running.
/opt/parking-certbot/bin/certbot certonly --non-interactive --agree-tos \
  --register-unsafely-without-email --webroot \
  --webroot-path /var/www/acme -d "$PUBLIC_HOST" --cert-name parking
cat > /etc/nginx/sites-available/parking <<EOF
server {
  listen 80 default_server;
  server_name $PUBLIC_HOST;
  location /.well-known/acme-challenge/ { root /var/www/acme; }
  location / { return 301 https://$PUBLIC_HOST\$request_uri; }
}
server {
  listen 443 ssl default_server;
  server_name $PUBLIC_HOST;
  ssl_certificate /etc/letsencrypt/live/parking/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/parking/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  client_max_body_size 16k;
  access_log off;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-For \$remote_addr;
  }
}
EOF
install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx <<'EOF'
#!/bin/sh
nginx -t && systemctl reload nginx
EOF
chmod 755 /etc/letsencrypt/renewal-hooks/deploy/reload-nginx
cat > /etc/systemd/system/parking-cert-renew.service <<'EOF'
[Unit]
Description=Renew parking HTTPS certificate
[Service]
Type=oneshot
ExecStart=/opt/parking-certbot/bin/certbot renew --quiet
EOF
cat > /etc/systemd/system/parking-cert-renew.timer <<'EOF'
[Unit]
Description=Check parking certificate renewal every six hours
[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
RandomizedDelaySec=900
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now smart-campus-parking parking-cert-renew.timer
nginx -t
systemctl reload nginx
echo "Installed commit $RELEASE_SHA. Verify https://$PUBLIC_HOST/api/health before declaring deployment complete."
echo 'Create the administrator privately using the documented operator command.'
