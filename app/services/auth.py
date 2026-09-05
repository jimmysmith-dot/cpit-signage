import json
import secrets
from functools import wraps
from pathlib import Path

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash

BASE_DIR = Path('/opt/cpit-signage')
AUTH_CONFIG_PATH = BASE_DIR / 'config' / 'admin_auth.json'


def load_auth_config():
    if not AUTH_CONFIG_PATH.is_file():
        return None

    try:
        data = json.loads(AUTH_CONFIG_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None

    username = str(data.get('username', '')).strip()
    password_hash = str(data.get('password_hash', '')).strip()
    secret_key = str(data.get('secret_key', '')).strip()

    if not username or not password_hash or not secret_key:
        return None

    return {
        'username': username,
        'password_hash': password_hash,
        'secret_key': secret_key,
    }


def get_secret_key():
    config = load_auth_config()
    if config:
        return config['secret_key']

    # Keeps the app able to start before initial auth setup.
    # Sessions created with this temporary key will not survive a restart.
    return secrets.token_hex(32)


def authentication_configured():
    return load_auth_config() is not None


def verify_credentials(username, password):
    config = load_auth_config()
    if not config:
        return False

    return (
        secrets.compare_digest(str(username), config['username'])
        and check_password_hash(config['password_hash'], str(password))
    )


def is_authenticated():
    return bool(session.get('studio_authenticated'))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('admin.login', next=request.path))
        return view(*args, **kwargs)

    return wrapped
