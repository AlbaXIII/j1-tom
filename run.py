import os
from dotenv import load_dotenv
import requests
import json
from flask import Flask, render_template
import frontmatter
import markdown
from datetime import datetime

load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("API_SPORTS_KEY")


def get_fixtures(league_id, season=2027):
    """Fetch fixtures from API-Sports"""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Fixtures API Response: {data}")

        if data["response"]:
            fixtures_by_round = {}
            for fixture in data["response"]:
                round_name = fixture["league"]["round"]
                if round_name not in fixtures_by_round:
                    fixtures_by_round[round_name] = []
                fixtures_by_round[round_name].append(fixture)

            return fixtures_by_round
        return None
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return None


def get_team_form_lookup(league_id, season=2027):
    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        form_lookup = {}

        if data["response"] and len(data["response"]) > 0:
            all_standings = data["response"][0]["league"]["standings"]
            for conference in all_standings:
                for team in conference:
                    form_lookup[team["team"]["name"]] = team.get("form", "")
        else:
            print(f"No form data for season {season}, trying {season-1}...")
            params["season"] = season - 1
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if data["response"] and len(data["response"]) > 0:
                all_standings = data["response"][0]["league"]["standings"]
                for conference in all_standings:
                    for team in conference:
                        form_lookup[team["team"]["name"]] = team.get("form", "")

        print(f"Form lookup result: {form_lookup}")  # Debug
        return form_lookup

    except Exception as e:
        print(f"Error fetching form data: {e}")
        return {}


def get_top_scorers(league_id, season=2027):
    """Fetch top scorers from API-Sports"""
    url = "https://v3.football.api-sports.io/players/topscorers"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Top Scorers API Response: {data}")

        if data["response"]:
            return data["response"][:20]
        return None
    except Exception as e:
        print(f"Error fetching top scorers: {e}")
        return None


def get_top_assists(league_id, season=2027):
    """Fetch top assists from API-Sports"""
    url = "https://v3.football.api-sports.io/players/topassists"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Top Assists API Response: {data}")

        if data["response"]:
            return data["response"][:20]
        return None
    except Exception as e:
        print(f"Error fetching top assists: {e}")
        return None


def get_standings(league_id, season=2027):
    """Fetch standings from API-Sports"""
    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"Standings API Response for season {season}: {data}")

        if data["response"] and len(data["response"]) > 0:
            all_standings = data["response"][0]["league"]["standings"]

            if len(all_standings) > 1:
                return {"conferences": all_standings, "has_conferences": True}
            else:
                return {"conferences": [all_standings[0]], "has_conferences": False}
        else:
            print(f"No standings data for season {season}, trying {season-1}")
            params["season"] = season - 1
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if data["response"] and len(data["response"]) > 0:
                print(f"Using {season-1} season data as fallback")
                return {
                    "conferences": [data["response"][0]["league"]["standings"][0]],
                    "has_conferences": False,
                }
        return None
    except Exception as e:
        print(f"Error fetching standings: {e}")
        return None


def get_all_posts():
    """Load all blog posts from the posts folder, sorted by date (newest first)"""
    posts = []
    posts_dir = "data/posts"

    if not os.path.exists(posts_dir):
        return posts

    for filename in os.listdir(posts_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(posts_dir, filename)
            post = frontmatter.load(filepath)
            posts.append(
                {
                    "slug": filename.replace(".md", ""),
                    "title": post.get("title", "Untitled"),
                    "date": post.get("date"),
                    "author": post.get("author", "Unknown"),
                    "tags": post.get("tags", []),
                    "excerpt": post.get("excerpt", ""),
                    "content": post.content,
                }
            )

    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def get_post_by_slug(slug):
    """Load a single post by its filename slug"""
    filepath = f"data/posts/{slug}.md"

    if not os.path.exists(filepath):
        return None

    post = frontmatter.load(filepath)
    html_content = markdown.markdown(post.content)

    return {
        "slug": slug,
        "title": post.get("title", "Untitled"),
        "date": post.get("date"),
        "author": post.get("author", "Unknown"),
        "tags": post.get("tags", []),
        "content": html_content,
    }


@app.route("/")
def index():
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []
    except json.JSONDecodeError:
        teams = []

    team_lookup = {team["name"]: team["team_id"] for team in teams}

    fixtures_by_round = get_fixtures(98, season=2027)
    form_lookup = get_team_form_lookup(98, season=2027)

    return render_template(
        "index.html",
        teams=teams,
        fixtures=fixtures_by_round,
        team_lookup=team_lookup,
        form_lookup=form_lookup,
    )


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

        team = next((t for t in teams if int(t["team_id"]) == team_id), None)

        if team:
            return render_template("team_detail.html", team=team)
        else:
            return "Team not found", 404
    except FileNotFoundError:
        return "Teams data not found", 404


@app.route("/stats")
def stats():
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []

    team_lookup = {team["name"]: team["team_id"] for team in teams}

    top_scorers = get_top_scorers(98, season=2027)
    top_assists = get_top_assists(98, season=2027)

    return render_template(
        "stats.html",
        top_scorers=top_scorers,
        top_assists=top_assists,
        team_lookup=team_lookup,
    )


@app.route("/standings")
def standings():
    import json

    try:
        with open("data/teams.json", "r", encoding="utf-8") as json_data:
            teams = json.load(json_data)
    except FileNotFoundError:
        teams = []

    team_lookup = {team["name"]: team["team_id"] for team in teams}

    standings_data = get_standings(98, season=2027)

    return render_template(
        "standings.html", standings=standings_data, team_lookup=team_lookup
    )


@app.route("/blog")
def blog():
    posts = get_all_posts()
    return render_template("blog.html", posts=posts)


@app.route("/blog/<slug>")
def blog_post(slug):
    post = get_post_by_slug(slug)
    if not post:
        return "Post not found", 404
    return render_template("blog_post.html", post=post)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
    )
