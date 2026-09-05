from pathlib import Path
import tempfile
from uuid import uuid4

from flask import Blueprint, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from app.services.database import (
    ASSET_TYPE_BACKGROUND,
    ASSET_TYPE_PLAYLIST,
    MEDIA_DIR,
    SUPPORTED_ASSET_TYPES,
    create_media_item,
    delete_media_item,
    get_all_media,
    get_enabled_slides,
    get_media_by_asset_type,
    get_media_item,
    reorder_media_items,
    update_media_item,
)
from app.services.slide_generator import (
    SlideGenerationError,
    create_sign_slide,
)
from app.services.sign_templates import (
    get_sign_template,
    get_sign_templates,
)
from app.services.template_packs import (
    TemplatePackError,
    get_pack_background_path,
    get_installed_template_packs,
    install_template_pack_zip,
    uninstall_template_pack,
)
from app.services.logo_tools import (
    LOGO_POSITIONS,
    LogoProcessingError,
    load_logo,
    normalize_position,
    normalize_width_percent,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGO_DIR = PROJECT_ROOT / "branding" / "logos"

ALLOWED_LOGO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def serialize_media(record):
    """Convert a SQLite row into JSON-safe media data."""
    return {
        "id": record["id"],
        "filename": record["filename"],
        "type": record["media_type"],
        "asset_type": record["asset_type"],
        "url": f"/media/{record['filename']}",
        "duration": record["duration"],
        "sort_order": record["sort_order"],
        "enabled": bool(record["enabled"]),
        "created_at": record["created_at"],
    }


def serialize_logo(path: Path):
    """Convert a stored logo path into JSON-safe logo data."""
    return {
        "filename": path.name,
        "url": f"/api/logos/{path.name}",
        "size_bytes": path.stat().st_size,
    }


@api_bp.route("/template-packs", methods=["GET"])
def template_pack_list():
    return jsonify(get_installed_template_packs())


@api_bp.route("/template-packs/install", methods=["POST"])
def template_pack_install():
    if "file" not in request.files:
        return jsonify({"error": "No template pack ZIP was included"}), 400
    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No template pack ZIP was selected"}), 400
    if Path(uploaded.filename).suffix.lower() != ".zip":
        return jsonify({"error": "Template packs must be ZIP files"}), 400

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
            temporary_path = Path(handle.name)
            uploaded.save(handle)
        pack = install_template_pack_zip(temporary_path)
        return jsonify({
            "message": f"Template pack '{pack['name']}' installed.",
            "pack": pack,
        }), 201
    except TemplatePackError as error:
        return jsonify({"error": str(error)}), 400
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@api_bp.route("/template-packs/<string:pack_id>", methods=["DELETE"])
def template_pack_delete(pack_id):
    try:
        pack = uninstall_template_pack(pack_id)
        return jsonify({"message": f"Template pack '{pack['name']}' removed."})
    except TemplatePackError as error:
        return jsonify({"error": str(error)}), 400


@api_bp.route("/sign-templates", methods=["GET"])
def sign_template_list():
    """Return all built-in sign templates."""
    return jsonify(get_sign_templates())


@api_bp.route(
    "/sign-templates/<string:template_id>",
    methods=["GET"],
)
def sign_template_detail(template_id):
    """Return one built-in sign template."""
    template = get_sign_template(template_id)

    if template is None:
        return jsonify({
            "error": "Sign template not found"
        }), 404

    return jsonify(template)


@api_bp.route(
    "/template-packs/<string:pack_id>/backgrounds/<path:filename>",
    methods=["GET"],
)
def template_pack_background(pack_id, filename):
    """Serve a bundled template-pack background image."""
    background_path = get_pack_background_path(
        pack_id,
        filename,
    )

    if background_path is None:
        return jsonify({
            "error": "Template pack background not found"
        }), 404

    return send_from_directory(
        background_path.parent,
        background_path.name,
        conditional=True,
    )


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

    records = get_media_by_asset_type(
        ASSET_TYPE_PLAYLIST
    )

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

    show_divider = data.get("show_divider", True)

    if not isinstance(show_divider, bool):
       show_divider = str(show_divider).strip().lower() in {
           "true", "1", "yes", "on"
       }

    duration_value = data.get("duration", 10)
    background_media_id = data.get("background_media_id")
    background_pack_asset = str(
        data.get("background_pack_asset", "")
    ).strip()
    overlay_value = data.get("overlay_opacity", 35)

    logo_filename = str(
        data.get("logo_filename", "")
    ).strip()

    logo_position_value = str(
        data.get("logo_position", "top-right")
    ).strip().lower()

    logo_width_value = data.get("logo_width_percent", 18)
    logo_margin_value = data.get("logo_margin", 70)

    position_defaults = {
        "title_x": 50.0, "title_y": 38.0,
        "body_x": 50.0, "body_y": 58.0,
        "footer_x": 50.0, "footer_y": 90.0,
    }
    text_positions = {}
    for field, default in position_defaults.items():
        try:
            value = float(data.get(field, default))
        except (TypeError, ValueError):
            return jsonify({"error": f"{field} must be a number"}), 400
        if value < 0 or value > 100:
            return jsonify({"error": f"{field} must be between 0 and 100"}), 400
        text_positions[field] = value

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

    if background_media_id not in (None, "") and background_pack_asset:
        return jsonify({
            "error": (
                "Choose either a media-library background "
                "or a template-pack background, not both."
            )
        }), 400

    if background_pack_asset:
        if ":" not in background_pack_asset:
            return jsonify({
                "error": "Template pack background reference is invalid"
            }), 400

        pack_id, background_filename = (
            background_pack_asset.split(":", 1)
        )

        background_image_path = get_pack_background_path(
            pack_id,
            background_filename,
        )

        if background_image_path is None:
            return jsonify({
                "error": "Template pack background was not found"
            }), 404

    elif background_media_id not in (None, ""):
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

        if (
            background_record["asset_type"]
            != ASSET_TYPE_BACKGROUND
        ):
            return jsonify({
                "error": (
                    "Selected media is not in the "
                    "background library"
                )
            }), 400

        background_image_path = (
            Path(MEDIA_DIR)
            / background_record["filename"]
        )

        if not background_image_path.is_file():
            return jsonify({
                "error": "Selected background image file is missing"
            }), 404

    logo_path = None
    logo_position = normalize_position(logo_position_value)

    try:
        logo_width_percent = normalize_width_percent(
            logo_width_value
        )
    except LogoProcessingError as error:
        return jsonify({
            "error": str(error)
        }), 400

    try:
        logo_margin = int(logo_margin_value)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Logo margin must be an integer"
        }), 400

    if logo_margin < 0 or logo_margin > 300:
        return jsonify({
            "error": "Logo margin must be between 0 and 300 pixels"
        }), 400

    if logo_filename:
        safe_logo_filename = secure_filename(logo_filename)

        if safe_logo_filename != logo_filename:
            return jsonify({
                "error": "The selected logo filename is invalid"
            }), 400

        logo_path = LOGO_DIR / safe_logo_filename

        if not logo_path.is_file():
            return jsonify({
                "error": "Selected logo was not found"
            }), 404

        try:
            load_logo(logo_path)
        except LogoProcessingError as error:
            return jsonify({
                "error": str(error)
            }), 400

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
            show_divider=show_divider,
            background_image_path=background_image_path,
            overlay_opacity=overlay_opacity,
            logo_path=logo_path,
            logo_position=logo_position,
            logo_width_percent=logo_width_percent,
            logo_margin=logo_margin,
            title_x=text_positions["title_x"],
            title_y=text_positions["title_y"],
            body_x=text_positions["body_x"],
            body_y=text_positions["body_y"],
            footer_x=text_positions["footer_x"],
            footer_y=text_positions["footer_y"],
        )

        record = create_media_item(
            filename=generated_path.name,
            media_type="image",
            asset_type=ASSET_TYPE_PLAYLIST,
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


@api_bp.route("/logos", methods=["GET"])
def logo_list():
    """Return all reusable branding logos."""
    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    logos = [
        serialize_logo(path)
        for path in sorted(
            LOGO_DIR.iterdir(),
            key=lambda item: item.name.lower(),
        )
        if (
            path.is_file()
            and path.suffix.lower() in ALLOWED_LOGO_EXTENSIONS
        )
    ]

    return jsonify(logos)


@api_bp.route("/logos", methods=["POST"])
def logo_upload():
    """Validate and store one reusable branding logo."""
    if "file" not in request.files:
        return jsonify({
            "error": "No logo file was included in the request"
        }), 400

    uploaded_file = request.files["file"]

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({
            "error": "No logo file was selected"
        }), 400

    original_name = secure_filename(uploaded_file.filename)

    if not original_name:
        return jsonify({
            "error": "The logo filename is invalid"
        }), 400

    original_path = Path(original_name)
    extension = original_path.suffix.lower()

    if extension not in ALLOWED_LOGO_EXTENSIONS:
        return jsonify({
            "error": "Unsupported logo file type",
            "allowed_extensions": sorted(
                ALLOWED_LOGO_EXTENSIONS
            ),
        }), 400

    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{original_path.stem}-{uuid4().hex[:8]}"
        f"{extension}"
    )

    final_path = LOGO_DIR / filename
    temporary_path = LOGO_DIR / f".uploading-{uuid4().hex}"

    try:
        uploaded_file.save(temporary_path)

        # load_logo performs format, dimensions, and image validation.
        load_logo(temporary_path)

        temporary_path.replace(final_path)

        return jsonify(serialize_logo(final_path)), 201

    except LogoProcessingError as error:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": str(error)
        }), 400

    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The logo could not be stored",
            "details": str(error),
        }), 500

    except Exception as error:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)

        return jsonify({
            "error": "The logo upload failed",
            "details": str(error),
        }), 500


@api_bp.route(
    "/logos/<path:filename>",
    methods=["GET"],
)
def logo_file(filename):
    """Serve one stored logo for previews and selection."""
    safe_filename = secure_filename(filename)

    if safe_filename != filename:
        return jsonify({
            "error": "Logo filename is invalid"
        }), 400

    logo_path = LOGO_DIR / safe_filename

    if not logo_path.is_file():
        return jsonify({
            "error": "Logo not found"
        }), 404

    return send_from_directory(
        LOGO_DIR,
        safe_filename,
        conditional=True,
    )


@api_bp.route(
    "/logos/<path:filename>",
    methods=["DELETE"],
)
def logo_delete(filename):
    """Delete one reusable branding logo."""
    safe_filename = secure_filename(filename)

    if safe_filename != filename:
        return jsonify({
            "error": "Logo filename is invalid"
        }), 400

    logo_path = LOGO_DIR / safe_filename

    if not logo_path.is_file():
        return jsonify({
            "error": "Logo not found"
        }), 404

    try:
        logo_path.unlink()
    except OSError as error:
        return jsonify({
            "error": "The logo could not be deleted",
            "details": str(error),
        }), 500

    return jsonify({
        "deleted": True,
        "filename": safe_filename,
    })


@api_bp.route("/media", methods=["GET"])
def media_list():
    asset_type = str(
        request.args.get("asset_type", "")
    ).strip().lower()

    if asset_type:
        if asset_type not in SUPPORTED_ASSET_TYPES:
            return jsonify({
                "error": "Asset type must be playlist or background",
                "allowed_asset_types": sorted(
                    SUPPORTED_ASSET_TYPES
                ),
            }), 400

        records = get_media_by_asset_type(asset_type)
    else:
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

    asset_type = str(
        request.form.get(
            "asset_type",
            ASSET_TYPE_PLAYLIST,
        )
    ).strip().lower()

    if asset_type not in SUPPORTED_ASSET_TYPES:
        return jsonify({
            "error": "Asset type must be playlist or background",
            "allowed_asset_types": sorted(
                SUPPORTED_ASSET_TYPES
            ),
        }), 400

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
            asset_type=asset_type,
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
