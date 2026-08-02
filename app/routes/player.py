from flask import Blueprint, render_template, send_from_directory

from app.services.database import MEDIA_DIR

player_bp = Blueprint("player", __name__)


@player_bp.route("/")
def index():
    return render_template("index.html")


@player_bp.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_DIR, filename)
