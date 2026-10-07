"""LED Planner account/licence service. Serve behind HTTPS on one origin."""
import calendar
import hashlib
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit

import click
from flask import Flask, g, jsonify, request, send_from_directory, redirect, make_response
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
PLANS = ('trial', 'monthly', 'yearly', 'permanent')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 pin_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
 plan TEXT NOT NULL, start_mode TEXT NOT NULL, starts_at INTEGER, expires_at INTEGER,
 enabled INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 csrf TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, until_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, at INTEGER NOT NULL);
'''

def expiry(start, plan):
    if plan == 'permanent':
        return None
    if plan == 'trial':
        return start + 72 * 3600
    dt = datetime.fromtimestamp(start, timezone.utc)
    month = dt.month + (1 if plan == 'monthly' else 12)
    year = dt.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return int(dt.replace(year=year, month=month,
                          day=min(dt.day, calendar.monthrange(year, month)[1])).timestamp())


def public_user(row, now):
    u = {k: row[k] for k in ('id', 'username', 'name', 'role', 'plan', 'start_mode', 'starts_at', 'expires_at', 'enabled', 'created_at')}
    if not u['enabled']:
        status = 'disabled'
    elif u['starts_at'] is None:
        status = 'pending'
    elif u['starts_at'] > now:
        status = 'scheduled'
    elif u['expires_at'] is not None and u['expires_at'] <= now:
        status = 'expired'
    else:
        status = 'active'
    u['status'] = status
    u['access'] = bool(u['enabled'] and (u['role'] == 'admin' or status == 'active'))
    return u


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(DATABASE=os.environ.get('LED_DATABASE', str(ROOT / 'data' / 'ledplanner.sqlite')),
                      PUBLIC_ORIGIN=os.environ.get('LED_PUBLIC_ORIGIN', 'http://127.0.0.1:8000').rstrip('/'),
                      COOKIE_SECURE=os.environ.get('LED_DEV_HTTP') != '1',
                      WHATSAPP=os.environ.get('LED_WHATSAPP', ''), MAX_CONTENT_LENGTH=16_384,
                      CLOCK=time.time)
    if config:
        app.config.update(config)
    origin = urlsplit(app.config['PUBLIC_ORIGIN'])
    if origin.scheme not in ('https', 'http') or not origin.netloc or origin.path:
        raise ValueError('LED_PUBLIC_ORIGIN harus berupa origin tanpa path.')
    if app.config['COOKIE_SECURE'] and origin.scheme != 'https':
        raise ValueError('Gunakan HTTPS; LED_DEV_HTTP=1 hanya untuk pengujian lokal.')
    app.config['TRUSTED_HOSTS'] = [origin.hostname]
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.executescript(SCHEMA)
        conn.execute('PRAGMA journal_mode=WAL')
    dummy_hash = generate_password_hash(secrets.token_urlsafe(24), method='scrypt')

    def now():
        return int(app.config['CLOCK']())

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=20)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(_):
        conn = g.pop('db', None)
        if conn:
            conn.close()

    def fail(message, status=400):
        return jsonify(error=message), status

    def audit(action, target):
        db().execute('INSERT INTO audit(actor,action,target,at) VALUES(?,?,?,?)',
                     (g.user['id'], action, target, now()))

    def current_session():
        token = request.cookies.get('led_session', '')
        if not token or len(token) > 100:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        session = db().execute('SELECT * FROM sessions WHERE token_hash=? AND expires_at>?', (digest, now())).fetchone()
        if session:
            user = db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if user and user['enabled']:
                g.user, g.session = user, session
                return session
        return None

    def require(admin=False):
        def decorate(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if not current_session():
                    return fail('Silakan login kembali.', 401)
                if admin and g.user['role'] != 'admin':
                    return fail('Akses hanya untuk admin.', 403)
                if request.method not in ('GET', 'HEAD') and not secrets.compare_digest(
                        request.headers.get('X-CSRF-Token', ''), g.session['csrf']):
                    return fail('Sesi formulir tidak valid. Muat ulang halaman.', 403)
                return fn(*args, **kwargs)
            return wrapped
        return decorate

    @app.before_request
    def same_origin():
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if request.headers.get('Origin') != app.config['PUBLIC_ORIGIN']:
                return fail('Origin tidak diizinkan.', 403)
            if not request.is_json:
                return fail('Gunakan JSON.', 415)

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
        if app.config['COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.errorhandler(413)
    def too_large(_):
        return fail('Data permintaan terlalu besar.', 413)

    @app.get('/')
    def portal():
        return send_from_directory(ROOT / 'web', 'portal.html')

    @app.get('/portal/<path:name>')
    def portal_file(name):
        if name not in ('portal.js', 'portal.css'):
            return fail('Tidak ditemukan.', 404)
        return send_from_directory(ROOT / 'web', name)

    @app.get('/assets/<path:name>')
    def assets(name):
        if Path(name).suffix.lower() not in ('.png', '.jpg', '.jpeg', '.svg', '.ico', '.webp'):
            return fail('Tidak ditemukan.', 404)
        return send_from_directory(ROOT.parent / 'assets', name)

    @app.get('/planner')
    def planner():
        if not current_session() or not public_user(g.user, now())['access']:
            return redirect('/')
        html = (ROOT.parent / 'index.html').read_text()
        # Projects belong to the account on this browser. Never adopt another account's data.
        html = html.replace('ledplanner-v3', 'ledplanner-user-' + g.user['id'])
        html = html.replace('ledplanner-v1', 'ledplanner-unused-' + g.user['id'])
        html = html.replace('<script>', '<script>document.getElementById("brandSplash")?.remove();', 1)
        return make_response(html)

    @app.get('/api/config')
    def config_route():
        phone = app.config['WHATSAPP']
        return jsonify(whatsapp=phone if re.fullmatch(r'[1-9][0-9]{7,14}', phone) else '')

    def reserve_attempt(bucket, limit):
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM attempts WHERE bucket=?', (bucket,)).fetchone()
        if row and row['until_at'] > now() and row['count'] >= limit:
            conn.rollback()
            return False
        count = row['count'] + 1 if row and row['until_at'] > now() else 1
        until = row['until_at'] if row and row['until_at'] > now() else now() + 900
        conn.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)', (bucket, count, until))
        conn.execute('DELETE FROM attempts WHERE until_at<?', (now() - 86400,))
        conn.commit()
        return True

    @app.post('/api/login')
    def login():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return fail('Form login tidak valid.')
        username, pin = str(data.get('username', '')).lower().strip(), str(data.get('pin', ''))
        # Do not trust arbitrary X-Forwarded-For headers. Configure the trusted proxy in production.
        ip_key = 'ip:' + hashlib.sha256((request.remote_addr or '').encode()).hexdigest()
        user_key = 'user:' + hashlib.sha256(username.encode()).hexdigest()
        if not reserve_attempt(ip_key, 60) or not reserve_attempt(user_key, 10):
            return fail('Terlalu banyak percobaan. Coba lagi dalam 15 menit.', 429)
        user = db().execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        valid = check_password_hash(user['pin_hash'] if user else dummy_hash, pin[:128])
        if not valid or not user or not user['enabled']:
            return fail('Username atau PIN salah, atau akun dinonaktifkan.', 401)
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        user = conn.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone()
        # Recheck after acquiring the write lock (admin may disable/reset concurrently).
        if not user['enabled'] or not check_password_hash(user['pin_hash'], pin[:128]):
            conn.rollback()
            return fail('Login tidak valid. Silakan coba lagi.', 401)
        if user['starts_at'] is None:
            start = now()
            conn.execute('UPDATE users SET starts_at=?,expires_at=? WHERE id=?', (start, expiry(start, user['plan']), user['id']))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        conn.execute('DELETE FROM sessions WHERE expires_at<=?', (now(),))
        # One browser session per account. A new login revokes previous sessions.
        conn.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
        conn.execute('INSERT INTO sessions VALUES(?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user['id'], csrf, now() + 86400))
        conn.execute('DELETE FROM attempts WHERE bucket=?', (user_key,))
        conn.commit()
        result = public_user(conn.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone(), now())
        response = jsonify(user=result, csrf=csrf, server_time=now())
        response.set_cookie('led_session', token, max_age=86400, httponly=True, secure=app.config['COOKIE_SECURE'], samesite='Strict', path='/')
        return response

    @app.get('/api/session')
    @require()
    def session_route():
        return jsonify(user=public_user(g.user, now()), csrf=g.session['csrf'], server_time=now())

    @app.post('/api/logout')
    @require()
    def logout():
        db().execute('DELETE FROM sessions WHERE token_hash=?', (g.session['token_hash'],))
        db().commit()
        response = jsonify(ok=True)
        response.delete_cookie('led_session', path='/')
        return response

    def validate_pin(data):
        if data.get('pin_mode') == 'auto':
            return ''.join(secrets.choice('0123456789') for _ in range(8))
        pin = data.get('pin', '')
        if not isinstance(pin, str) or not re.fullmatch(r'[0-9]{6,12}', pin):
            raise ValueError('PIN manual harus 6–12 digit.')
        return pin

    def license_values(data):
        plan = data.get('plan')
        if plan not in PLANS:
            raise ValueError('Pilih paket akses yang valid.')
        mode = data.get('start_mode', 'first_login')
        if mode == 'first_login':
            return plan, mode, None, None
        if mode != 'scheduled':
            raise ValueError('Mode aktivasi tidak valid.')
        try:
            start = int(data.get('starts_at'))
            dt = datetime.fromtimestamp(start, timezone.utc)
            if not 2020 <= dt.year <= 2100:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            raise ValueError('Tanggal mulai tidak valid.')
        return plan, mode, start, expiry(start, plan)

    @app.get('/api/admin/users')
    @require(admin=True)
    def users():
        return jsonify(users=[public_user(r, now()) for r in db().execute("SELECT * FROM users WHERE role='user' ORDER BY created_at DESC")])

    @app.post('/api/admin/users')
    @require(admin=True)
    def create_user():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return fail('Form tidak valid.')
        try:
            username = str(data.get('username', '')).strip().lower()
            name = str(data.get('name', '')).strip()
            if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,39}', username) or not 1 <= len(name) <= 100:
                raise ValueError('Nama wajib diisi. Username 3–40 karakter: huruf, angka, titik, _ atau -.')
            pin = validate_pin(data)
            plan, mode, start, end = license_values(data)
            uid = secrets.token_hex(16)
            db().execute('INSERT INTO users(id,username,name,pin_hash,plan,start_mode,starts_at,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                         (uid, username, name, generate_password_hash(pin, method='scrypt'), plan, mode, start, end, now()))
            audit('create_user', uid)
            db().commit()
        except ValueError as e:
            return fail(str(e))
        except sqlite3.IntegrityError:
            db().rollback()
            return fail('Username sudah digunakan.', 409)
        return jsonify(user=public_user(db().execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone(), now()), pin=pin), 201

    @app.post('/api/admin/users/<uid>')
    @require(admin=True)
    def change_user(uid):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return fail('Form tidak valid.')
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        target = conn.execute("SELECT * FROM users WHERE id=? AND role='user'", (uid,)).fetchone()
        if not target:
            conn.rollback()
            return fail('Pengguna tidak ditemukan.', 404)
        action, pin = data.get('action'), None
        try:
            if action == 'reset_pin':
                pin = validate_pin(data)
                conn.execute('UPDATE users SET pin_hash=? WHERE id=?', (generate_password_hash(pin, method='scrypt'), uid))
            elif action == 'enabled':
                if not isinstance(data.get('enabled'), bool):
                    raise ValueError('Status akun tidak valid.')
                conn.execute('UPDATE users SET enabled=? WHERE id=?', (int(data['enabled']), uid))
            elif action == 'license':
                plan, mode, start, end = license_values(data)
                conn.execute('UPDATE users SET plan=?,start_mode=?,starts_at=?,expires_at=? WHERE id=?', (plan, mode, start, end, uid))
            elif action == 'extend':
                if target['plan'] == 'permanent' or target['starts_at'] is None or target['starts_at'] > now():
                    raise ValueError('Perpanjangan berlaku untuk paket berjangka yang sudah mulai. Gunakan Ubah paket untuk akun ini.')
                end = expiry(max(now(), target['expires_at'] or now()), target['plan'])
                conn.execute('UPDATE users SET expires_at=? WHERE id=?', (end, uid))
            elif action != 'reset_session':
                raise ValueError('Tindakan tidak valid.')
            if action in ('reset_pin', 'enabled', 'license', 'reset_session'):
                conn.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            audit(action, uid)
            conn.commit()
        except ValueError as e:
            conn.rollback()
            return fail(str(e))
        return jsonify(user=public_user(conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone(), now()), **({'pin': pin} if pin else {}))

    @app.cli.command('create-admin')
    @click.option('--username', default='hdrg', prompt=True)
    @click.password_option(prompt='PIN admin baru (8–12 digit)')
    def create_admin(username, password):
        """Create the first administrator on the server. No default credential."""
        username = username.strip().lower()
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,39}', username) or not re.fullmatch(r'[0-9]{8,12}', password):
            raise click.ClickException('Username atau PIN tidak valid. PIN admin 8–12 digit.')
        if db().execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            raise click.ClickException('Admin sudah ada. Pembuatan admin awal tidak dapat diulang.')
        db().execute("INSERT INTO users(id,username,name,pin_hash,role,plan,start_mode,starts_at,created_at) VALUES(?,?,?,?, 'admin','permanent','scheduled',?,?)",
                     (secrets.token_hex(16), username, 'Administrator HDRG', generate_password_hash(password, method='scrypt'), now(), now()))
        db().commit()
        click.echo('Admin dibuat. PIN tidak disimpan dalam bentuk teks.')

    return app
