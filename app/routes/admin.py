from flask import Blueprint, redirect, render_template, request, url_for

from app.services.database import get_all_media, update_media_item

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin():
    media_items = get_all_media()

    return render_template(
        "admin.html",
        media_items=media_items,
        saved=request.args.get("saved") == "1",
    )


@admin_bp.route("/save", methods=["POST"])
def save():
    media_items = get_all_media()

    for item in media_items:
        media_id = item["id"]

        duration_value = request.form.get(
            f"duration_{media_id}",
            item["duration"],
        )

        order_value = request.form.get(
            f"order_{media_id}",
            item["sort_order"],
        )

        enabled_value = (
            request.form.get(f"enabled_{media_id}") == "on"
        )

        try:
            update_media_item(
                media_id=media_id,
                duration=int(duration_value),
                sort_order=int(order_value),
                enabled=enabled_value,
            )
        except (TypeError, ValueError):
            continue

    return redirect(url_for("admin.admin", saved=1))
