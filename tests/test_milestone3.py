from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.models import classes, lots, lot_updates, users
from app.seed import seed_demo
from test_project import app, login, token

def test_versioned_upgrade_preserves_existing_records(tmp_path):
    url='sqlite:///'+str(tmp_path/'upgrade.db').replace('\\','/')
    engine=create_engine(url)
    cfg=Config();cfg.set_main_option('script_location',str(Path(__file__).resolve().parents[1]/'migrations'))
    with engine.begin() as c:
        cfg.attributes['connection']=c
        command.upgrade(cfg,'0001_initial')
        seed_demo(c)
        c.execute(lots.update().where(lots.c.lot_id==2).values(available_spaces=7))
        assert 'lot_update' not in inspect(c).get_table_names()
    engine.dispose()
    upgraded=create_app({'TESTING':True,'DATABASE_URL':url})
    with upgraded.extensions['db'].connect() as c:
        assert c.execute(text('SELECT version_num FROM alembic_version')).scalar_one()=='0002_lot_audit'
        assert c.execute(select(lots.c.available_spaces).where(lots.c.lot_id==2)).scalar_one()==7
        assert c.execute(select(users.c.email).where(users.c.user_id==1)).scalar_one()=='alex@example.test'
        assert 'lot_update' in inspect(c).get_table_names()
    upgraded.extensions['db'].dispose()

def test_class_and_permit_survive_restart(app):
    c,h=login(app)
    assert c.patch('/api/me/permit',json={'permit_id':2},headers=h).status_code==200
    r=c.post('/api/classes',json=dict(title='Persistent class',weekday=4,start_time='12:00',end_time='13:00',building_id=1),headers=h)
    cid=r.json['class_id']
    url=app.config['DATABASE_URL'];app.extensions['db'].dispose()
    restarted=create_app(dict(TESTING=True,SECRET_KEY='test-only',DATABASE_URL=url))
    try:
        c,_=login(restarted)
        assert c.get('/api/me').json['permit_id']==2
        assert any(x['class_id']==cid and x['title']=='Persistent class' for x in c.get('/api/classes').json)
    finally: restarted.extensions['db'].dispose()

def test_status_change_preserves_count_timestamp_and_audits(app):
    c,h=login(app,'jordan@example.test')
    before=next(x for x in c.get('/api/admin/lots').json if x['lot_id']==2)
    after=c.patch('/api/admin/lots/2',json={'status':'closed'},headers=h).json
    assert after['updated_at']==before['updated_at']
    with app.extensions['db'].connect() as conn:
        row=conn.execute(select(lot_updates)).mappings().one()
        assert row['actor_id']==2 and row['lot_id']==2 and 'closed' in row['changes_json']

def test_invalid_update_does_not_create_audit_record(app):
    c,h=login(app,'jordan@example.test')
    assert c.patch('/api/admin/lots/2',json={'available_spaces':999},headers=h).status_code==400
    with app.extensions['db'].connect() as conn:
        assert conn.execute(select(lot_updates)).first() is None

def test_foreign_key_enforced(app):
    with pytest.raises(IntegrityError):
        with app.extensions['db'].begin() as c:
            c.execute(users.update().where(users.c.user_id==1).values(permit_id=999))

def test_future_class_is_provisional_and_permits_are_named(app):
    app.config['NOW']=lambda:datetime(2026,10,6,23,0,tzinfo=ZoneInfo('America/New_York'))
    c,_=login(app);data=c.get('/api/recommendations').json
    assert data['provisional'] is True
    assert data['recommendation']['accepted_permits']==['Student']

@pytest.mark.parametrize('change',[{'weekday':7},{'building_id':999},{'title':''},{'start_time':'abc'},{'unknown':1}])
def test_invalid_class_update_keeps_original(app,change):
    c,h=login(app);before=c.get('/api/classes').json
    assert c.patch('/api/classes/1',json=change,headers=h).status_code==400
    assert c.get('/api/classes').json==before

def test_bad_registration_and_json(app):
    c=app.test_client();h=token(c)
    assert c.post('/api/auth/register',json={'email':'bad','password':'long-enough-password'},headers=h).status_code==400
    assert c.post('/api/auth/register',json={'email':'new@example.test','password':'short'},headers=h).status_code==400
    assert c.post('/api/auth/login',json=[],headers=h).status_code==400

def test_invalid_permit_selection(app):
    c,h=login(app)
    assert c.patch('/api/me/permit',json={'permit_id':999},headers=h).status_code==400
    assert c.get('/api/me').json['permit_id']==1

def test_refuse_unversioned_database_without_mutating_it(tmp_path):
    url='sqlite:///'+str(tmp_path/'legacy.db').replace('\\','/')
    e=create_engine(url)
    with e.begin() as c:c.exec_driver_sql('CREATE TABLE important_data (value TEXT)')
    with pytest.raises(RuntimeError,match='Unversioned database'):
        create_app({'DATABASE_URL':url})
    with e.connect() as c: assert inspect(c).get_table_names()==['important_data']
    e.dispose()
