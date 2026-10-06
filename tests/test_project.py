from datetime import datetime, time
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.models import metadata, users, classes, lots, walks
from app.seed import seed_demo
from app.services import get_next_class
FIXED=datetime(2026,10,6,9,0,tzinfo=ZoneInfo("America/New_York"))

@pytest.fixture()
def app(tmp_path):
    app=create_app(dict(TESTING=True,SECRET_KEY="test-only",DATABASE_URL="sqlite:///"+str(tmp_path/"test.db").replace("\\","/"),NOW=lambda:FIXED))
    engine=app.extensions["db"];metadata.create_all(engine)
    with engine.begin() as conn: seed_demo(conn)
    yield app
    engine.dispose()

def token(client):
    return {"X-CSRF-Token":client.get("/api/auth/csrf").json["csrf_token"]}
def login(app,email="alex@example.test"):
    c=app.test_client()
    r=c.post("/api/auth/login",json=dict(email=email,password="DemoParking123!"),headers=token(c))
    assert r.status_code==200
    return c,{"X-CSRF-Token":r.json["csrf_token"]}

def test_page_and_health(app):
    c=app.test_client()
    assert b"Campus parking" in c.get("/").data
    assert c.get("/static/app.js").status_code==200
    assert c.get("/api/health").json=={"status":"ok"}

def test_closure_changes_recommendation(app):
    student,_=login(app); admin,h=login(app,"jordan@example.test")
    before=student.get("/api/recommendations").json
    assert before["recommendation"]["name"]=="Lot B"
    assert before["recommendation"]["parked_by"]=="2026-10-06T09:50:00-04:00"
    assert admin.patch("/api/admin/lots/2",json={"status":"closed"},headers=h).status_code==200
    after=student.get("/api/recommendations").json
    assert after["recommendation"]["name"]=="Lot A"
    assert [x["name"] for x in after["alternatives"]]==[]

def test_full_lot_excluded(app):
    with app.extensions["db"].begin() as conn: conn.execute(lots.update().where(lots.c.lot_id==2).values(available_spaces=0))
    c,_=login(app)
    assert c.get("/api/recommendations").json["recommendation"]["name"]=="Lot A"

def test_wrong_permit_and_closed_lot_excluded(app):
    c,_=login(app);result=c.get("/api/recommendations").json
    assert [result["recommendation"]["name"]]+[x["name"] for x in result["alternatives"]]==["Lot B","Lot A"]

def test_no_eligible_lot(app):
    with app.extensions["db"].begin() as conn: conn.execute(lots.update().values(status="closed"))
    c,_=login(app);result=c.get("/api/recommendations").json
    assert result["recommendation"] is None and result["reason"]=="no_eligible_lot"

def test_missing_permit(app):
    with app.extensions["db"].begin() as conn: conn.execute(users.update().where(users.c.user_id==1).values(permit_id=None))
    c,_=login(app)
    assert c.get("/api/recommendations").json["reason"]=="permit_required"

def test_no_upcoming_class(app):
    with app.extensions["db"].begin() as conn: conn.execute(classes.delete())
    c,_=login(app)
    assert c.get("/api/recommendations").json["reason"]=="no_upcoming_class"

def test_week_boundary(app):
    with app.extensions["db"].begin() as conn:
        conn.execute(classes.delete().where(classes.c.weekday!=0))
        result=get_next_class(conn,1,datetime(2026,10,11,23,0,tzinfo=ZoneInfo("America/New_York")))
        assert result["starts_at"]=="2026-10-12T10:00:00-04:00"

def test_ranking_tie_break(app):
    with app.extensions["db"].begin() as conn:
        conn.execute(walks.update().where(walks.c.lot_id==1).values(walking_minutes=5))
        conn.execute(lots.update().where(lots.c.lot_id==1).values(available_spaces=18))
    c,_=login(app)
    assert c.get("/api/recommendations").json["recommendation"]["lot_id"]==1

@pytest.mark.parametrize("value",[-1,51,True,"18",1.5])
def test_invalid_space_counts(app,value):
    c,h=login(app,"jordan@example.test")
    assert c.patch("/api/admin/lots/2",json={"available_spaces":value},headers=h).status_code==400
    assert next(x for x in c.get("/api/admin/lots").json if x["lot_id"]==2)["available_spaces"]==18

def test_student_cannot_admin(app):
    c,h=login(app)
    assert c.patch("/api/admin/lots/2",json={"status":"closed"},headers=h).status_code==403
    assert c.get("/api/admin/lots").status_code==403

def test_missing_csrf(app):
    c,_=login(app)
    assert c.patch("/api/me/permit",json={"permit_id":2}).status_code==403

def test_login_required(app):
    assert app.test_client().get("/api/classes").status_code==401

def test_wrong_password(app):
    c=app.test_client()
    assert c.post("/api/auth/login",json=dict(email="alex@example.test",password="wrong"),headers=token(c)).status_code==401

def test_schedule_crud(app):
    c,h=login(app)
    r=c.post("/api/classes",json=dict(title="Databases",weekday=3,start_time="12:00",end_time="13:00",building_id=1),headers=h)
    assert r.status_code==201;cid=r.json["class_id"]
    assert c.patch("/api/classes/"+str(cid),json={"title":"Database Systems"},headers=h).status_code==200
    assert next(x for x in c.get("/api/classes").json if x["class_id"]==cid)["title"]=="Database Systems"
    assert c.delete("/api/classes/"+str(cid),headers=h).status_code==204

def test_class_ownership(app):
    c,h=login(app,"jordan@example.test")
    assert c.patch("/api/classes/1",json={"title":"No"},headers=h).status_code==404
    assert c.delete("/api/classes/1",headers=h).status_code==404

def test_invalid_class_times(app):
    c,h=login(app)
    assert c.post("/api/classes",json=dict(title="X",weekday=1,start_time="11:00",end_time="10:00",building_id=1),headers=h).status_code==400

def test_permit_rules_change(app):
    admin,h=login(app,"jordan@example.test");student,_=login(app)
    assert admin.put("/api/admin/lots/2/permits",json={"permit_ids":[]},headers=h).status_code==200
    assert student.get("/api/recommendations").json["recommendation"]["name"]=="Lot A"

def test_invalid_permit_rules_rollback(app):
    c,h=login(app,"jordan@example.test")
    assert c.put("/api/admin/lots/2/permits",json={"permit_ids":[999]},headers=h).status_code==400
    assert next(x for x in c.get("/api/admin/lots").json if x["lot_id"]==2)["permit_ids"]==[1]

def test_registration_and_hash(app):
    c=app.test_client();h=token(c)
    data=dict(email="new@example.test",password="NewStudent123!")
    assert c.post("/api/auth/register",json=data,headers=h).status_code==201
    assert c.post("/api/auth/register",json=data,headers=h).status_code==409
    with app.extensions["db"].connect() as conn:
        row=conn.execute(select(users).where(users.c.email==data["email"])).mappings().one()
        assert row["role"]=="student" and row["password_hash"]!=data["password"]

def test_no_admin_registration(app):
    c=app.test_client()
    assert c.post("/api/auth/register",json=dict(email="hack@example.test",password="LongPassword123!",role="admin"),headers=token(c)).status_code==400

def test_logout(app):
    c,h=login(app)
    assert c.post("/api/auth/logout",json={},headers=h).status_code==204
    assert c.get("/api/me").status_code==401

def test_database_constraints(app):
    with pytest.raises(IntegrityError):
        with app.extensions["db"].begin() as conn: conn.execute(lots.update().where(lots.c.lot_id==2).values(available_spaces=500))

def test_schema_initialization_and_seed_guard(app):
    runner=app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code==0
    assert runner.invoke(args=["seed-demo"]).exit_code!=0
    with app.extensions["db"].connect() as conn: assert len(conn.execute(select(users)).all())==2

