import sqlite3
from datetime import datetime, timezone
import pytest
from werkzeug.security import generate_password_hash
from licensing.app import create_app, expiry

ORIGIN='http://localhost'
@pytest.fixture
def env(tmp_path):
    clock=[1800000000]
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.sqlite'),'PUBLIC_ORIGIN':ORIGIN,'COOKIE_SECURE':False,'CLOCK':lambda:clock[0]})
    with sqlite3.connect(app.config['DATABASE']) as c:
        c.execute("INSERT INTO users(id,username,name,pin_hash,role,plan,start_mode,starts_at,created_at) VALUES('admin','hdrg','HDRG',?,'admin','permanent','scheduled',?,?)",(generate_password_hash('98765432'),clock[0],clock[0]))
    client=app.test_client()
    r=post(client,'/api/login',{'username':'hdrg','pin':'98765432'})
    assert r.status_code==200
    return app,client,r.json['csrf'],clock

def post(client,path,data,csrf=''):
    return client.post(path,json=data,headers={'Origin':ORIGIN,'X-CSRF-Token':csrf})

def user(env,**kw):
    _,c,csrf,_=env
    r=post(c,'/api/admin/users',dict(name='Rental ABC',username='rentalabc',pin_mode='manual',pin='12345678',plan='trial',start_mode='first_login',**kw),csrf)
    assert r.status_code==201,r.json
    return r.json

def login(app,pin='12345678'):
    c=app.test_client();r=post(c,'/api/login',{'username':'rentalabc','pin':pin});return c,r

def test_trial_activation_and_expiry(env):
    app,admin,csrf,clock=env
    result=user(env)
    assert result['user']['starts_at'] is None
    clock[0]+=86400
    c,r=login(app)
    assert r.json['user']['expires_at']==clock[0]+72*3600
    assert c.get('/planner').status_code==200
    start=r.json['user']['starts_at']
    clock[0]+=3*86400
    c,r=login(app)
    assert r.json['user']['status']=='expired'
    assert r.json['user']['starts_at']==start
    assert c.get('/planner').status_code==302

def test_admin_authorization_and_csrf(env):
    app,admin,csrf,_=env
    user(env)
    c,r=login(app)
    assert c.get('/api/admin/users').status_code==403
    assert post(c,'/api/admin/users',{},r.json['csrf']).status_code==403
    assert post(admin,'/api/admin/users',{}).status_code==403
    assert admin.post('/api/admin/users',json={},headers={'Origin':'https://evil.example','X-CSRF-Token':csrf}).status_code==403
    assert app.test_client().get('/api/admin/users').status_code==401
    assert app.test_client().get('/planner').status_code==302
    assert app.test_client().get('/index.html').status_code==404

def test_hashes_auto_pin_and_duplicate(env):
    app,admin,csrf,_=env
    r=post(admin,'/api/admin/users',{'name':'Auto','username':'auto','pin_mode':'auto','plan':'permanent','start_mode':'first_login'},csrf)
    assert r.status_code==201
    pin=r.json['pin'];assert len(pin)==8 and pin.isdigit()
    with sqlite3.connect(app.config['DATABASE']) as c:
        hashed=c.execute("SELECT pin_hash FROM users WHERE username='auto'").fetchone()[0]
        assert hashed.startswith('scrypt:') and pin not in hashed
    listed=admin.get('/api/admin/users').json
    assert 'pin' not in listed['users'][0] and 'pin_hash' not in listed['users'][0]
    assert post(admin,'/api/admin/users',{'name':'Auto','username':'auto','pin_mode':'auto','plan':'permanent'},csrf).status_code==409

def test_reset_disable_and_session_revocation(env):
    app,admin,csrf,_=env;uid=user(env)['user']['id'];c,r=login(app)
    url='/api/admin/users/'+uid
    result=post(admin,url,{'action':'reset_pin','pin_mode':'auto'},csrf)
    assert result.status_code==200
    assert c.get('/api/session').status_code==401
    assert login(app)[1].status_code==401
    c,r=login(app,result.json['pin']);assert r.status_code==200
    assert post(admin,url,{'action':'enabled','enabled':False},csrf).status_code==200
    assert c.get('/api/session').status_code==401
    assert login(app,result.json['pin'])[1].status_code==401

def test_one_session(env):
    app,_,_,_=env;user(env)
    c,_=login(app);other,r=login(app)
    assert c.get('/api/session').status_code==401
    assert other.get('/api/session').status_code==200

def test_calendar_boundaries():
    stamp=lambda y,m,d:int(datetime(y,m,d,12,tzinfo=timezone.utc).timestamp())
    assert expiry(stamp(2028,1,31),'monthly')==stamp(2028,2,29)
    assert expiry(stamp(2028,2,29),'yearly')==stamp(2029,2,28)
    assert expiry(stamp(2028,12,31),'monthly')==stamp(2029,1,31)
    assert expiry(stamp(2028,1,31),'permanent') is None

def test_extend_preserves_remaining_time(env):
    app,admin,csrf,clock=env;uid=user(env)['user']['id'];c,r=login(app)
    end=r.json['user']['expires_at'];clock[0]+=3600
    r=post(admin,'/api/admin/users/'+uid,{'action':'extend'},csrf)
    assert r.json['user']['expires_at']==end+72*3600
    clock[0]=r.json['user']['expires_at']+3600
    renewed=post(admin,'/api/login',{'username':'hdrg','pin':'98765432'})
    csrf=renewed.json['csrf']
    r=post(admin,'/api/admin/users/'+uid,{'action':'extend'},csrf)
    assert r.json['user']['expires_at']==clock[0]+72*3600

def test_scheduled_and_permanent(env):
    app,admin,csrf,clock=env
    r=post(admin,'/api/admin/users',{'name':'Future','username':'rentalabc','pin_mode':'manual','pin':'12345678','plan':'permanent','start_mode':'scheduled','starts_at':clock[0]+100},csrf)
    assert r.status_code==201
    c,r=login(app);assert r.json['user']['status']=='scheduled'
    assert c.get('/planner').status_code==302
    clock[0]+=100
    assert c.get('/api/session').json['user']['access']
    assert c.get('/api/session').json['user']['expires_at'] is None

def test_rate_limit(env):
    app,_,_,_=env;user(env);c=app.test_client()
    for _ in range(10):
        assert post(c,'/api/login',{'username':'rentalabc','pin':'00000000'}).status_code==401
    assert post(c,'/api/login',{'username':'rentalabc','pin':'12345678'}).status_code==429

def test_invalid_input_and_no_admin_mutation(env):
    _,admin,csrf,_=env
    assert post(admin,'/api/admin/users',{'name':'Bad','username':'bad','pin_mode':'manual','pin':'1945','plan':'trial'},csrf).status_code==400
    assert post(admin,'/api/admin/users/admin',{'action':'enabled','enabled':False},csrf).status_code==404
    assert post(admin,'/api/admin/users',[],csrf).status_code==400

def test_isolated_project_storage_and_logout(env):
    app,_,_,_=env;uid=user(env)['user']['id'];c,r=login(app)
    html=c.get('/planner').text
    assert 'ledplanner-user-'+uid in html
    assert "localStorage.getItem('ledplanner-v1')" not in html
    assert "localStorage.getItem('ledplanner-v3')" not in html
    assert post(c,'/api/logout',{},r.json['csrf']).status_code==200
    assert c.get('/api/session').status_code==401

def test_production_cookie_and_cli(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'prod.sqlite'),'PUBLIC_ORIGIN':'https://localhost','COOKIE_SECURE':True})
    runner=app.test_cli_runner();r=runner.invoke(args=['create-admin','--username','hdrg','--password','12349876'])
    assert r.exit_code==0
    c=app.test_client();r=c.post('/api/login',json={'username':'hdrg','pin':'12349876'},headers={'Origin':'https://localhost'},base_url='https://localhost')
    cookie=r.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Strict' in cookie
    assert runner.invoke(args=['create-admin','--username','other','--password','12349876']).exit_code!=0
