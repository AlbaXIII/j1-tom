import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/teams")
def teams():
    return render_template("teams.html")


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/standings")
def standings():
    return render_template("standings.html")


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True
    )
