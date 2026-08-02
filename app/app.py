from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from database import (
    MEDIA_DIR,
    get_all_media,
    get_enabled_slides,
    import_existing_media,
    update_media_item,
)

BASE_DIR = Path("/opt/cpit-signage")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "app/templates"),
    static_folder=str(BASE_DIR / "app/static"),
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/slides")
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


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_DIR, filename)


@app.route("/admin")
def admin():
    media_items = get_all_media()

    return render_template(
        "admin.html",
        media_items=media_items,
        saved=request.args.get("saved") == "1",
    )


@app.route("/admin/save", methods=["POST"])
def admin_save():
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

        enabled_value = request.form.get(
            f"enabled_{media_id}"
        ) == "on"

        try:
            update_media_item(
                media_id=media_id,
                duration=int(duration_value),
                sort_order=int(order_value),
                enabled=enabled_value,
            )
        except (TypeError, ValueError):
            continue

    return redirect(url_for("admin", saved=1))


if __name__ == "__main__":
    import_existing_media()
    app.run(host="127.0.0.1", port=5000)
