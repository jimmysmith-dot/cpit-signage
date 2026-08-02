from pathlib import Path
from uuid import uuid4


from flask import Blueprint, jsonify, request
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from app.services.database import (
    MEDIA_DIR,
    create_media_item,
    delete_media_item,
    get_all_media,
    get_enabled_slides,
    get_media_item,
    reorder_media_items,
    update_media_item,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")
ALLOWED_IMAGE_EXTENSIONS = {
	".jpg",
	".jpeg",
	".png",
	".gif",
	".webp",
}

def serialize_media(record):
    """Convert a SQLite row into JSON-safe media data."""
    return {
        "id": record["id"],
        "filename": record["filename"],
        "type": record["media_type"],
        "url": f"/media/{record['filename']}",
        "duration": record["duration"],
        "sort_order": record["sort_order"],
        "enabled": bool(record["enabled"]),
        "created_at": record["created_at"],
    }



@api_bp.route("/media/reorder", methods=["PUT"])
def media_reorder():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    media_ids = data.get("media_ids")

    if not isinstance(media_ids, list) or not media_ids:
        return jsonify({
            "error": "media_ids must be a non-empty array"
        }), 400

    try:
        if any(media_id is None for media_id in media_ids):
            raise ValueError(
                "The reorder list contains a missing media ID"
            )

        normalized_ids = [
            int(media_id)
            for media_id in media_ids
        ]

        reorder_media_items(normalized_ids)

    except (TypeError, ValueError) as error:
        return jsonify({
            "error": str(error)
        }), 400

    records = get_all_media()

    return jsonify([
        serialize_media(record)
        for record in records
    ])

@api_bp.route("/slides", methods=["GET"])
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


@api_bp.route("/media", methods=["GET"])
def media_list():
    records = get_all_media()

    return jsonify([
        serialize_media(record)
        for record in records
    ])
@api_bp.route("/media", methods=["POST"])
def media_upload():
    if "file" not in request.files:
        return jsonify({
            "error": "No file was included in the request"
        }), 400

    uploaded_file = request.files["file"]

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({
            "error": "No file was selected"
        }), 400

    original_name = secure_filename(uploaded_file.filename)

    if not original_name:
        return jsonify({
            "error": "The filename is invalid"
        }), 400

    original_path = Path(original_name)
    extension = original_path.suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({
            "error": "Unsupported file type",
            "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS),
        }), 400

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    unique_suffix = uuid4().hex[:8]
    filename = (
        f"{original_path.stem}-{unique_suffix}{extension}"
    )

    final_path = MEDIA_DIR / filename
    temporary_path = MEDIA_DIR / f".uploading-{uuid4().hex}"

    try:
        uploaded_file.save(temporary_path)

        with Image.open(temporary_path) as image:
            image.verify()

        temporary_path.replace(final_path)

        record = create_media_item(
            filename=filename,
            media_type="image",
            duration=10,
            enabled=True,
        )

        return jsonify(serialize_media(record)), 201

    except UnidentifiedImageError:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The uploaded file is not a valid image"
        }), 400

    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The image could not be stored",
            "details": str(error),
        }), 500

    except Exception as error:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The upload failed",
            "details": str(error),
        }), 500


@api_bp.route("/media/<int:media_id>", methods=["GET"])
def media_detail(media_id):
    record = get_media_item(media_id)

    if record is None:
        return jsonify({
            "error": "Media item not found"
        }), 404

    return jsonify(serialize_media(record))


@api_bp.route("/media/<int:media_id>", methods=["PUT"])
def media_update(media_id):
    record = get_media_item(media_id)

    if record is None:
        return jsonify({
            "error": "Media item not found"
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    duration = data.get("duration", record["duration"])
    sort_order = data.get("sort_order", record["sort_order"])
    enabled = data.get("enabled", bool(record["enabled"]))

    try:
        duration = int(duration)
        sort_order = int(sort_order)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Duration and sort_order must be integers"
        }), 400

    if not isinstance(enabled, bool):
        return jsonify({
            "error": "Enabled must be true or false"
        }), 400

    if duration < 1 or duration > 3600:
        return jsonify({
            "error": "Duration must be between 1 and 3600 seconds"
        }), 400

    if sort_order < 0:
        return jsonify({
            "error": "Sort order cannot be negative"
        }), 400

    update_media_item(
        media_id=media_id,
        duration=duration,
        sort_order=sort_order,
        enabled=enabled,
    )

    updated_record = get_media_item(media_id)

    return jsonify(serialize_media(updated_record))


@api_bp.route("/media/<int:media_id>", methods=["DELETE"])
def media_delete(media_id):
    record = get_media_item(media_id)

    if record is None:
        return jsonify({
            "error": "Media item not found"
        }), 404

    media_path = Path(MEDIA_DIR) / record["filename"]

    deleted = delete_media_item(media_id)

    if not deleted:
        return jsonify({
            "error": "Unable to delete media record"
        }), 500

    file_deleted = False

    try:
        if media_path.is_file():
            media_path.unlink()
            file_deleted = True
    except OSError as error:
        return jsonify({
            "error": "Database record deleted, but file removal failed",
            "details": str(error),
            "id": media_id,
            "filename": record["filename"],
        }), 500

    return jsonify({
        "deleted": True,
        "file_deleted": file_deleted,
        "id": media_id,
        "filename": record["filename"],
    })
