"""Exercise the real browser -> HTTP -> persistent SQLite workflow and capture evidence."""
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from urllib.request import urlopen
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'/'browser';OUT.mkdir(parents=True,exist_ok=True)
TMP=Path(tempfile.mkdtemp(prefix='browser-',dir=OUT))
DB=TMP/'parking.db'
env=os.environ.copy();env.update(DATABASE_URL='sqlite:///'+DB.as_posix(),SECRET_KEY='browser-test-only-secret')
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
URL=f'http://127.0.0.1:{port}'
log=(OUT/'startup.log').open('w',encoding='utf-8')
process=None

def start():
    p=subprocess.Popen([sys.executable,'-m','flask','--app','app:create_app','run','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=log)
    for _ in range(100):
        if p.poll() is not None:raise RuntimeError('Server failed; inspect startup.log')
        try:
            if urlopen(URL+'/api/health',timeout=1).status==200:return p
        except OSError:time.sleep(.1)
    p.terminate();raise RuntimeError('Server startup timed out')

def sign_in(page,email):
    page.goto(URL)
    page.get_by_label('Email',exact=True).fill(email)
    page.get_by_label('Password',exact=True).fill('DemoParking123!')
    page.get_by_role('button',name='Sign in',exact=True).click()
    expect(page.locator('#dashboard')).to_be_visible()

def screenshot(page,name):
    page.screenshot(path=str(OUT/name),full_page=True)

try:
    subprocess.run([sys.executable,'-m','flask','--app','app:create_app','seed-demo'],cwd=ROOT,env=env,stdout=log,stderr=log,check=True)
    process=start()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,channel=os.environ.get('BROWSER_CHANNEL') or None)
        context=browser.new_context(viewport={'width':1100,'height':900},device_scale_factor=1)
        context.set_default_timeout(10000)
        page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(URL)
        page.get_by_role('button',name='Create a student account').click()
        page.get_by_label('Email',exact=True).fill('mvp@example.test')
        page.get_by_label('Password',exact=True).fill('DemoParking123!')
        page.get_by_role('button',name='Create account',exact=True).click()
        expect(page.locator('#dashboard')).to_be_visible()
        page.get_by_label('Permit type',exact=True).select_option('1')
        page.get_by_role('button',name='Save permit',exact=True).click()
        expect(page.locator('#message')).to_have_text('Permit saved.')
        tomorrow=datetime.now(ZoneInfo('America/New_York'))+timedelta(days=1)
        form=page.locator('#class-form')
        form.get_by_label('Class name').fill('Database Systems')
        form.get_by_label('Day',exact=True).select_option(str(tomorrow.weekday()))
        form.get_by_label('Building',exact=True).select_option('1')
        form.get_by_label('Start time').fill('10:00')
        form.get_by_label('End time').fill('11:00')
        form.get_by_role('button',name='Add class',exact=True).click()
        expect(page.locator('#classes')).to_contain_text('Database Systems')
        expect(page.locator('#recommendation h3')).to_have_text('Lot B')
        screenshot(page,'01-student-saved.png')
        page.locator('#recommendation').screenshot(path=str(OUT/'student-plan.png'))
        page.locator('#classes').screenshot(path=str(OUT/'saved-schedule.png'))
        page.locator('#class-form').screenshot(path=str(OUT/'class-form.png'))
        with sqlite3.connect(DB) as conn:
            row=conn.execute('SELECT c.title,u.email,u.permit_id FROM class_session c JOIN user u ON u.user_id=c.user_id WHERE u.email=?',('mvp@example.test',)).fetchone()
            assert row==('Database Systems','mvp@example.test',1)
        # Restart the actual server process against the same file, then sign in again.
        process.terminate();process.wait(timeout=10);process=start()
        context.clear_cookies();sign_in(page,'mvp@example.test')
        expect(page.locator('#classes')).to_contain_text('Database Systems')
        expect(page.locator('#recommendation h3')).to_have_text('Lot B')
        screenshot(page,'02-after-restart.png')
        admin_context=browser.new_context(viewport={'width':1100,'height':900})
        admin_context.set_default_timeout(10000)
        admin=admin_context.new_page();sign_in(admin,'jordan@example.test')
        lot=admin.get_by_role('form',name='Lot B',exact=True)
        lot.get_by_label('Lot status').select_option('closed')
        lot.get_by_role('button',name='Save lot').click()
        expect(admin.locator('#message')).to_contain_text('Lot B saved')
        expect(admin.get_by_role('form',name='Lot B',exact=True).get_by_label('Lot status')).to_have_value('closed')
        screenshot(admin,'03-admin-closed.png')
        admin.get_by_role('form',name='Lot B',exact=True).screenshot(path=str(OUT/'admin-lot.png'))
        page.get_by_role('button',name='Refresh parking').click()
        expect(page.locator('#recommendation h3')).to_have_text('Lot A')
        screenshot(page,'04-student-updated.png')
        page.locator('#recommendation').screenshot(path=str(OUT/'updated-plan.png'))
        with sqlite3.connect(DB) as conn:
            closed=conn.execute('SELECT status FROM parking_lot WHERE lot_id=2').fetchone()[0]
            audit=conn.execute('SELECT lot_id,actor_id,changes_json FROM lot_update').fetchall()
            revision=conn.execute('SELECT version_num FROM alembic_version').fetchone()[0]
        assert closed=='closed' and len(audit)==1
        # Exercise editing, server-side validation, and deletion through the UI.
        page.locator('#classes').get_by_role('button',name='Edit',exact=True).click()
        form.get_by_label('End time').fill('09:00')
        form.get_by_role('button',name='Save changes').click()
        expect(page.locator('#message')).to_contain_text('end time after start time')
        form.get_by_label('End time').fill('11:00')
        form.get_by_label('Class name').fill('Database Systems Revised')
        form.get_by_role('button',name='Save changes').click()
        expect(page.locator('#classes')).to_contain_text('Database Systems Revised')
        page.on('dialog',lambda dialog:dialog.accept())
        page.locator('#classes').get_by_role('button',name='Delete',exact=True).click()
        expect(page.locator('#classes')).to_contain_text('Your schedule is empty')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        report={'result':'passed','checks':['student registration','permit persistence','class creation','Lot B recommendation','database row verified','server restart persistence','admin closure','Lot A after refresh','audit transaction','invalid edit rejected','valid edit','delete','mobile no overflow','no JavaScript errors'], 'schema_revision':revision,'saved_class_before_deletion':list(row),'admin_change':{'lot_id':2,'status':closed,'audit_rows':len(audit)},'database_type':'file-backed SQLite','timezone':'America/New_York'}
        (OUT/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
        browser.close()
finally:
    if process and process.poll() is None:process.terminate();process.wait(timeout=10)
    log.close()
