import os
import requests
import json
from flask import Flask, render_template

app = Flask(__name__)
API_KEY = os.getenv("API_SPORTS_KEY")


def get_fixtures(league_id, season=2026):
    """Fetch fixtures from API-Sports"""
    url = 'https://v3.football.api-sports.io/fixtures'
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Fixtures API Response: {data}")

        if data['response']:
            fixtures_by_round = {}
            for fixture in data['response']:
                round_name = fixture['league']['round']
                if round_name not in fixtures_by_round:
                    fixtures_by_round[round_name] = []
                fixtures_by_round[round_name].append(fixture)

            return fixtures_by_round
        return None
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return None


def get_standings(league_id, season=2026):
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
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []
        print("Warning: data/teams.json not found")
    except json.JSONDecodeError:
        teams = []
        print("Warning: Invalid JSON in teams.json")

    team_lookup = {team['name']: team['team_id'] for team in teams}

    fixtures_by_round = get_fixtures(98, season=2026)

    return render_template("index.html", teams=teams,
                           fixtures=fixtures_by_round,
                           team_lookup=team_lookup)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/teams")
def teams():
    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []
        print("Warning: data/teams.json not found")
    except json.JSONDecodeError:
        teams = []
        print("Warning: Invalid JSON in teams.json")
    return render_template("teams.html", teams=teams)


@app.route("/team/<int:team_id>")
def team_detail(team_id):
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)

        team = next((t for t in teams if int(t['team_id']) == team_id), None)

        if team:
            return render_template("team_detail.html", team=team)
        else:
            return "Team not found", 404
    except FileNotFoundError:
        return "Teams data not found", 404


@app.route("/stats")
def stats():
    return render_template("stats.html")


@app.route("/standings")
def standings():
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []

    team_lookup = {team['name']: team['team_id'] for team in teams}

    standings_data = get_standings(98, season=2026)

    return render_template("standings.html", 
                           standings=standings_data, team_lookup=team_lookup)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True
    )
