from flask import Flask, render_template

app = Flask(
    __name__,
    template_folder="/opt/cpit-signage/templates",
    static_folder="/opt/cpit-signage/static",
)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)