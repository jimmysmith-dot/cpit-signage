import getpass
import json
import secrets
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path('/opt/cpit-signage')
CONFIG_PATH = BASE_DIR / 'config' / 'admin_auth.json'


def main():
    print('CPIT Signage Studio - Administrator Setup')
    print()

    username = input('Administrator username [admin]: ').strip() or 'admin'

    while True:
        password = getpass.getpass('Password: ')
        confirmation = getpass.getpass('Confirm password: ')

        if not password:
            print('Password cannot be blank. Try again.')
            continue

        if password != confirmation:
            print('Passwords do not match. Try again.')
            continue

        break

    existing_secret = None
    if CONFIG_PATH.is_file():
        try:
            existing = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            existing_secret = str(existing.get('secret_key', '')).strip() or None
        except (OSError, json.JSONDecodeError):
            pass

    config = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'secret_key': existing_secret or secrets.token_hex(32),
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    CONFIG_PATH.chmod(0o600)

    print()
    print(f'Administrator account saved to {CONFIG_PATH}')
    print('Restart cpit-player to apply the session secret if this is first-time setup.')


if __name__ == '__main__':
    main()
