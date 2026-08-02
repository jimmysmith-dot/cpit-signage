from flask import Flask, render_template, jsonify
from pathlib import Path

BASE_DIR = Path("/opt/cpit-signage")
MEDIA_DIR = BASE_DIR / "media"

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
    images = []

    for ext in ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"):
        for file in sorted(MEDIA_DIR.glob(ext)):
            images.append({
                "type": "image",
                "url": f"/media/{file.name}",
                "duration": 10
            })

    return jsonify(images)

@app.route("/media/<path:filename>")
def media(filename):
    from flask import send_from_directory
    return send_from_directory(MEDIA_DIR, filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
