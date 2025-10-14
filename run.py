import os
import requests
from flask import Flask, render_template

app = Flask(__name__)
API_KEY = os.getenv("API_SPORTS_KEY")


def get_standings(league_id, season=2023):
    """Fetch standings from API-Sports"""
    url = 'https://v3.football.api-sports.io/standings'
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Standings API Response: {data}")

        if data['response'] and len(data['response']) > 0:
            return data['response'][0]['league']['standings'][0]
        return None
    except Exception as e:
        print(f"Error fetching standings: {e}")
        return None


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
    standings_data = get_standings(98, season=2023)
    return render_template("standings.html", standings=standings_data)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True
    )
