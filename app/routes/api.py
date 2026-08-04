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
from app.services.slide_generator import (
    SlideGenerationError,
    create_sign_slide,
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


@api_bp.route("/slides/create", methods=["POST"])
def create_slide():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    title = str(data.get("title", "")).strip()
    body = str(data.get("body", "")).strip()
    footer = str(data.get("footer", "")).strip()

    background_color = str(
        data.get("background_color", "#153A5B")
    ).strip()

    text_color = str(
        data.get("text_color", "#FFFFFF")
    ).strip()

    accent_color = str(
        data.get("accent_color", "#75B9E6")
    ).strip()

    alignment = str(
        data.get("alignment", "center")
    ).strip().lower()

    duration_value = data.get("duration", 10)
    background_media_id = data.get("background_media_id")
    overlay_value = data.get("overlay_opacity", 35)

    if not title and not body:
        return jsonify({
            "error": "A title or body message is required"
        }), 400

    if len(title) > 250:
        return jsonify({
            "error": "Title cannot exceed 250 characters"
        }), 400

    if len(body) > 2000:
        return jsonify({
            "error": "Body cannot exceed 2000 characters"
        }), 400

    if len(footer) > 500:
        return jsonify({
            "error": "Footer cannot exceed 500 characters"
        }), 400

    if alignment not in {"left", "center", "right"}:
        return jsonify({
            "error": "Alignment must be left, center, or right"
        }), 400

    try:
        duration = int(duration_value)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Duration must be an integer"
        }), 400

    if duration < 1 or duration > 3600:
        return jsonify({
            "error": "Duration must be between 1 and 3600 seconds"
        }), 400

    try:
        overlay_opacity = int(overlay_value)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Overlay opacity must be an integer"
        }), 400

    if overlay_opacity < 0 or overlay_opacity > 100:
        return jsonify({
            "error": "Overlay opacity must be between 0 and 100"
        }), 400

    background_image_path = None

    if background_media_id not in (None, ""):
        try:
            normalized_background_id = int(background_media_id)
        except (TypeError, ValueError):
            return jsonify({
                "error": "Background media ID must be an integer"
            }), 400

        background_record = get_media_item(
            normalized_background_id
        )

        if background_record is None:
            return jsonify({
                "error": "Selected background image was not found"
            }), 404

        if background_record["media_type"] != "image":
            return jsonify({
                "error": "Selected background must be image media"
            }), 400

        background_image_path = (
            Path(MEDIA_DIR)
            / background_record["filename"]
        )

        if not background_image_path.is_file():
            return jsonify({
                "error": "Selected background image file is missing"
            }), 404

    generated_path = None

    try:
        generated_path = create_sign_slide(
            output_directory=MEDIA_DIR,
            title=title,
            body=body,
            footer=footer,
            background_color=background_color,
            text_color=text_color,
            accent_color=accent_color,
            alignment=alignment,
            background_image_path=background_image_path,
            overlay_opacity=overlay_opacity,
        )

        record = create_media_item(
            filename=generated_path.name,
            media_type="image",
            duration=duration,
            enabled=True,
        )

        return jsonify({
            "message": "Slide created successfully",
            "media": serialize_media(record),
        }), 201

    except SlideGenerationError as error:
        if generated_path is not None:
            generated_path.unlink(missing_ok=True)

        return jsonify({
            "error": str(error)
        }), 400

    except Exception as error:
        if generated_path is not None:
            generated_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The slide could not be created",
            "details": str(error),
        }), 500


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
            "allowed_extensions": sorted(
                ALLOWED_IMAGE_EXTENSIONS
            ),
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

    duration = data.get(
        "duration",
        record["duration"],
    )

    sort_order = data.get(
        "sort_order",
        record["sort_order"],
    )

    enabled = data.get(
        "enabled",
        bool(record["enabled"]),
    )

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
            "error": (
                "Database record deleted, "
                "but file removal failed"
            ),
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
