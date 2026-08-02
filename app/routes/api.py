from flask import Blueprint, jsonify

from app.services.database import get_enabled_slides

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/slides")
def slides():
    records = get_enabled_slides()

    playlist = [
        {
            "id": record["id"],
            "type": record["media_type"],
            "url": f"/media/{record['filename']}",
            "duration": record["duration"],
            "sort_order": record["sort_order"],
        }
        for record in records
    ]

    return jsonify(playlist)
