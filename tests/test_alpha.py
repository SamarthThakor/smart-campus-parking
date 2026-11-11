"""Security regressions exercise real requests and persistent SQLite state."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select, text
from app import create_app
from app.models import users, classes, auth_sessions, auth_limits
from test_project import app, login, token


def test_export_contains_only_owner_data_and_no_credentials(app):
    c, _ = login(app)
    response = c.get("/api/me/export")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "attachment" in response.headers["Content-Disposition"]
    data = response.json
    assert data["account"]["email"] == "alex@example.test"
    assert all(row["user_id"] == 1 for row in data["classes"])
    assert "password_hash" not in response.text and "auth_token" not in response.text
    assert "jordan@example.test" not in response.text


def test_delete_requires_csrf_and_password_then_revokes_all_sessions(app):
    c, h = login(app)
    other, _ = login(app)
    assert c.delete("/api/me", json={"password": "DemoParking123!"}).status_code == 403
    assert c.delete("/api/me", json={"password": "wrong"}, headers=h).status_code == 401
    assert c.get("/api/me").status_code == 200
    assert (
        c.delete("/api/me", json={"password": "DemoParking123!"}, headers=h).status_code
        == 204
    )
    assert other.get("/api/me").status_code == 401
    with app.extensions["db"].connect() as conn:
        assert conn.execute(select(users).where(users.c.user_id == 1)).first() is None
        assert (
            conn.execute(select(classes).where(classes.c.user_id == 1)).first() is None
        )
        assert (
            conn.execute(
                select(auth_sessions).where(auth_sessions.c.user_id == 1)
            ).first()
            is None
        )


def test_admin_cannot_use_student_deletion(app):
    c, h = login(app, "jordan@example.test")
    assert (
        c.delete("/api/me", json={"password": "DemoParking123!"}, headers=h).status_code
        == 403
    )


def test_signed_out_cookie_cannot_be_replayed(app):
    c, h = login(app)
    stolen = c.get_cookie("session").value
    assert c.post("/api/auth/logout", json={}, headers=h).status_code == 204
    replay = app.test_client()
    replay.set_cookie("session", stolen)
    assert replay.get("/api/me").status_code == 401


def test_session_has_absolute_server_expiry(app):
    clock = [10000]
    app.config["AUTH_CLOCK"] = lambda: clock[0]
    c, _ = login(app)
    clock[0] += 3599
    assert c.get("/api/me").status_code == 200
    clock[0] += 1
    assert c.get("/api/me").status_code == 401


def test_login_limit_persists_across_app_restart_and_expires(app):
    clock = [18000]
    app.config.update(
        RATE_LIMIT_ENABLED=True, AUTH_ACCOUNT_LIMIT=2, AUTH_CLOCK=lambda: clock[0]
    )
    c = app.test_client()
    h = token(c)
    data = dict(email="alex@example.test", password="wrong")
    assert c.post("/api/auth/login", json=data, headers=h).status_code == 401
    assert c.post("/api/auth/login", json=data, headers=h).status_code == 401
    restarted = create_app(
        dict(
            TESTING=True,
            SECRET_KEY="test-only",
            DATABASE_URL=app.config["DATABASE_URL"],
            RATE_LIMIT_ENABLED=True,
            AUTH_ACCOUNT_LIMIT=2,
            AUTH_CLOCK=lambda: clock[0],
        )
    )
    try:
        c2 = restarted.test_client()
        blocked = c2.post("/api/auth/login", json=data, headers=token(c2))
        assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
        with restarted.extensions["db"].connect() as conn:
            rows = conn.execute(select(auth_limits)).mappings().all()
            assert all(len(row["key_hash"]) == 64 for row in rows)
            assert "alex" not in str(rows) and "127.0.0.1" not in str(rows)
        clock[0] += 901
        assert (
            c2.post("/api/auth/login", json=data, headers=token(c2)).status_code == 401
        )
    finally:
        restarted.extensions["db"].dispose()


def test_ip_limit_cannot_be_bypassed_by_forwarded_headers(app):
    app.config.update(RATE_LIMIT_ENABLED=True, AUTH_IP_LIMIT=1)
    c = app.test_client()
    h = token(c)
    assert (
        c.post(
            "/api/auth/login",
            json=dict(email="one@example.test", password="wrong"),
            headers=h,
        ).status_code
        == 401
    )
    h["X-Forwarded-For"] = "203.0.113.1"
    assert (
        c.post(
            "/api/auth/login",
            json=dict(email="two@example.test", password="wrong"),
            headers=h,
        ).status_code
        == 429
    )


def test_concurrent_authentication_counts_are_atomic(app):
    app.config.update(RATE_LIMIT_ENABLED=True, AUTH_ACCOUNT_LIMIT=2)

    def attempt(_):
        c = app.test_client()
        return c.post(
            "/api/auth/login",
            json=dict(email="missing@example.test", password="wrong"),
            headers=token(c),
        ).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))
    assert sorted(results) == [401, 401, 429, 429]


def test_browser_security_headers_and_private_cache(app):
    c = app.test_client()
    response = c.get("/")
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert c.get("/api/auth/csrf").headers["Cache-Control"] == "no-store"
    assert c.get("/privacy").status_code == 200


def test_production_rejects_unsafe_configuration(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(
            dict(
                APP_ENV="production",
                DATABASE_URL="sqlite:///" + str(tmp_path / "prod.db"),
            )
        )
    monkeypatch.setenv("SECRET_KEY", "a" * 40)
    with pytest.raises(RuntimeError, match="HTTPS"):
        create_app(dict(APP_ENV="production", SESSION_COOKIE_SECURE=False))


def test_production_hides_demo_and_enforces_hosts(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "b" * 40)
    prod = create_app(
        dict(
            TESTING=True,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            TRUSTED_HOSTS=["parking.example"],
            DATABASE_URL="sqlite:///" + str(tmp_path / "prod.db").replace("\\", "/"),
        )
    )
    try:
        c = prod.test_client()
        response = c.get("/", base_url="https://parking.example")
        assert response.status_code == 200
        assert "DemoParking123!" not in response.text
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
        csrf_response = c.get("/api/auth/csrf", base_url="https://parking.example")
        cookie = csrf_response.headers["Set-Cookie"]
        assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
        assert c.get("/", base_url="https://evil.example").status_code == 400
        assert prod.test_cli_runner().invoke(args=["seed-demo"]).exit_code != 0
    finally:
        prod.extensions["db"].dispose()


def test_injection_is_data_and_class_owner_cannot_be_overridden(app):
    c, h = login(app)
    payload = dict(
        title="<img src=x onerror=alert(1)> '; DROP TABLE user; --",
        weekday=2,
        start_time="12:00",
        end_time="13:00",
        building_id=1,
    )
    response = c.post("/api/classes", json=payload, headers=h)
    assert response.status_code == 201
    payload["user_id"] = 2
    assert c.post("/api/classes", json=payload, headers=h).status_code == 400
    with app.extensions["db"].connect() as conn:
        assert len(conn.execute(select(users)).all()) == 2
    assert any(
        row["class_id"] == response.json["class_id"] and row["title"].startswith("<img")
        for row in c.get("/api/classes").json
    )


def test_admin_history_and_permit_rule_audit(app):
    student, _ = login(app)
    assert student.get("/api/admin/history").status_code == 403
    admin, h = login(app, "jordan@example.test")
    assert (
        admin.put(
            "/api/admin/lots/2/permits", json={"permit_ids": [1, 2]}, headers=h
        ).status_code
        == 200
    )
    row = admin.get("/api/admin/history").json[0]
    assert row["actor_id"] == 2 and row["changes"] == {"permit_ids": [1, 2]}
    assert "password" not in json.dumps(row)


def test_oversize_and_malformed_requests(app):
    c, h = login(app)
    assert (
        c.post(
            "/api/classes", data="bad", content_type="application/json", headers=h
        ).status_code
        == 400
    )
    assert (
        c.post("/api/classes", json={"title": "x" * 20000}, headers=h).status_code
        == 413
    )
    assert (
        c.post(
            "/api/auth/login",
            json={"email": "alex@example.test", "password": "x" * 129},
            headers=h,
        ).status_code
        == 400
    )


def test_create_admin_command_does_not_promote_existing_accounts(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["create-admin", "--email", "operator@example.test"],
        input="NewOperator123!\nNewOperator123!\n",
    )
    assert result.exit_code == 0
    c, _ = login(app)
    assert c.get("/api/me").json["role"] == "student"
    result = runner.invoke(
        args=["create-admin", "--email", "alex@example.test"],
        input="NewOperator123!\nNewOperator123!\n",
    )
    assert result.exit_code != 0


def test_alpha_migration_preserves_ms3_records(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from pathlib import Path
    from app.seed import seed_demo

    url = "sqlite:///" + str(tmp_path / "ms3.db").replace("\\", "/")
    engine = create_engine(url)
    cfg = Config()
    cfg.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "0002_lot_audit")
        seed_demo(conn)
    engine.dispose()
    upgraded = create_app({"TESTING": True, "DATABASE_URL": url})
    try:
        with upgraded.extensions["db"].connect() as conn:
            assert (
                conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                == "0003_alpha_security"
            )
            assert (
                conn.execute(
                    select(users.c.email).where(users.c.user_id == 1)
                ).scalar_one()
                == "alex@example.test"
            )
            assert conn.execute(select(auth_sessions)).all() == []
    finally:
        upgraded.extensions["db"].dispose()


def test_catalog_initialization_is_idempotent_without_demo_accounts(tmp_path):
    from app.models import lots
    fresh = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///" + str(tmp_path / "catalog.db").replace("\\", "/")})
    try:
        runner = fresh.test_cli_runner()
        assert runner.invoke(args=["init-catalog"]).exit_code == 0
        assert runner.invoke(args=["init-catalog"]).exit_code == 0
        with fresh.extensions["db"].connect() as conn:
            assert len(conn.execute(select(lots)).all()) == 4
            assert conn.execute(select(users)).all() == []
    finally:
        fresh.extensions["db"].dispose()


def test_bad_operator_password_cannot_create_admin(app):
    result = app.test_cli_runner().invoke(args=["create-admin", "--email", "bad@example.test"], input="short\nshort\n")
    assert result.exit_code != 0
    with app.extensions["db"].connect() as conn:
        assert conn.execute(select(users).where(users.c.email == "bad@example.test")).first() is None
