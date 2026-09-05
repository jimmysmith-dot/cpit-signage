from datetime import timedelta
from pathlib import Path

from flask import Flask

from app.routes.admin import admin_bp
from app.routes.api import api_bp
from app.routes.player import player_bp
from app.services.auth import get_secret_key
from app.services.database import import_existing_media

BASE_DIR = Path('/opt/cpit-signage')


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / 'app/templates'),
        static_folder=str(BASE_DIR / 'app/static'),
    )

    app.config.update(
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        SECRET_KEY=get_secret_key(),
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    app.register_blueprint(player_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    import_existing_media()

    return app
