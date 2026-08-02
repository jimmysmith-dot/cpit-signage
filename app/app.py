from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

from database import (
    MEDIA_DIR,
    get_enabled_slides,
    import_existing_media,
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


if __name__ == "__main__":
    import_existing_media()
    app.run(host="127.0.0.1", port=5000)
