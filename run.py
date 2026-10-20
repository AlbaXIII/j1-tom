import os
from dotenv import load_dotenv
import requests
import json
from pathlib import Path
from flask import Flask, render_template
import frontmatter
import markdown
from datetime import datetime, timedelta, timezone

load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("API_SPORTS_KEY")

EVENTS_CACHE_DIR = Path("data/events_cache")
EVENTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
POSITIONS_CACHE_DIR = Path("data/positions_cache")
POSITIONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_fixtures(league_id, season=2027):
    """Fetch fixtures from API-Sports"""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if data["response"]:
            fixtures_by_round = {}
            for fixture in data["response"]:
                status = fixture["fixture"]["status"]["short"]
                if status in ["FT", "AET", "PEN"]:
                    fixture["events"] = get_fixture_events(fixture["fixture"]["id"])
                else:
                    fixture["events"] = []

                round_name = fixture["league"]["round"]
                if round_name not in fixtures_by_round:
                    fixtures_by_round[round_name] = []
                fixtures_by_round[round_name].append(fixture)

            def round_sort_key(round_name):
                dates = [m["fixture"]["date"] for m in fixtures_by_round[round_name]]
                return min(dates)

            sorted_round_names = sorted(fixtures_by_round.keys(), key=round_sort_key)

            fixtures_by_round = {
                name: fixtures_by_round[name] for name in sorted_round_names
            }

            RESULTS_BUFFER = timedelta(hours=48)
            MATCH_LENGTH = timedelta(hours=2)
            FINISHED = ["FT", "AET", "PEN"]
            now = datetime.now(timezone.utc)

            default_round_index = 0

            for i, round_name in enumerate(sorted_round_names):
                matches = fixtures_by_round[round_name]
                statuses = [m["fixture"]["status"]["short"] for m in matches]

                if any(s in ["NS", "1H", "2H", "HT"] for s in statuses):
                    default_round_index = i
                    break

                finished_kickoffs = [
                    datetime.fromisoformat(m["fixture"]["date"])
                    for m in matches
                    if m["fixture"]["status"]["short"] in FINISHED
                ]
                if finished_kickoffs:
                    last_kickoff = max(finished_kickoffs)
                    if now < last_kickoff + MATCH_LENGTH + RESULTS_BUFFER:
                        default_round_index = i
                        break

                default_round_index = i

            return fixtures_by_round, default_round_index
        return None, 0
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return None, 0


def get_fixture_events(fixture_id):
    cache_file = EVENTS_CACHE_DIR / f"{fixture_id}.json"

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    url = "https://v3.football.api-sports.io/fixtures/events"
    headers = {"x-apisports-key": API_KEY}
    params = {"fixture": fixture_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        events = data["response"] if data["response"] else []

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(events, f)

        return events
    except Exception as e:
        print(f"Error fetching events for fixture {fixture_id}: {e}")
        return []


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


def get_last_five_results(api_team_id):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"team": api_team_id, "league": 98, "last": 5}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        results = []
        for f in data.get("response", []):
            is_home = f["teams"]["home"]["id"] == api_team_id
            opponent = f["teams"]["away"] if is_home else f["teams"]["home"]
            goals_for = f["goals"]["home"] if is_home else f["goals"]["away"]
            goals_against = f["goals"]["away"] if is_home else f["goals"]["home"]

            if goals_for is None or goals_against is None:
                continue

            if goals_for > goals_against:
                result = "W"
            elif goals_for == goals_against:
                result = "D"
            else:
                result = "L"

            results.append(
                {
                    "result": result,
                    "opponent": opponent["name"],
                    "opponent_logo": opponent["logo"],
                    "score": f"{goals_for} - {goals_against}",
                    "venue": "H" if is_home else "A",
                    "date": datetime.fromisoformat(f["fixture"]["date"]).strftime(
                        "%d %b"
                    ),
                    "timestamp": f["fixture"]["timestamp"],
                }
            )

        # Oldest on the left, newest on the right (same convention as form guides)
        results.sort(key=lambda r: r["timestamp"])
        return results
    except Exception as e:
        print(f"Error fetching last 5 results: {e}")
        return []


def get_last_five_positions(api_team_id, current_season=2027):
    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": API_KEY}
    positions = []

    for season in range(current_season - 5, current_season):
        cache_file = POSITIONS_CACHE_DIR / f"{api_team_id}_{season}.json"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                rank = json.load(f)
        else:
            params = {"league": 98, "season": season, "team": api_team_id}
            try:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()

                # Don't cache failures (rate limits, plan restrictions, etc.)
                if data.get("errors"):
                    print(f"API error for season {season}: {data['errors']}")
                    continue

                rank = None
                if data["response"]:
                    for group in data["response"][0]["league"]["standings"]:
                        for team in group:
                            if team["team"]["id"] == api_team_id:
                                rank = team["rank"]

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(rank, f)
            except Exception as e:
                print(f"Error fetching position for season {season}: {e}")
                continue

        if rank is not None:
            positions.append({"season": season, "rank": rank})

    return positions


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
                    "image": post.get("image"),
                    "image_alt": post.get("image_alt", ""),
                    "image_credit": post.get("image_credit", ""),
                    "sub_image": post.get("sub_image"),
                    "sub_image_alt": post.get("sub_image_alt", ""),
                    "sub_image_credit": post.get("sub_image_credit", ""),
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
        "image": post.get("image"),
        "image_alt": post.get("image_alt", ""),
        "image_credit": post.get("image_credit", ""),
        "sub_image": post.get("sub_image"),
        "sub_image_alt": post.get("sub_image_alt", ""),
        "sub_image_credit": post.get("sub_image_credit", ""),
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

    fixtures_by_round, default_round_index = get_fixtures(98, season=2027)
    form_lookup = get_team_form_lookup(98, season=2027)

    return render_template(
        "index.html",
        teams=teams,
        fixtures=fixtures_by_round,
        team_lookup=team_lookup,
        form_lookup=form_lookup,
        default_round_index=default_round_index,
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
            last_five_results = get_last_five_results(team["api_team_id"])
            last_five_positions = get_last_five_positions(team["api_team_id"])
            return render_template(
                "team_detail.html",
                team=team,
                last_five_results=last_five_results,
                last_five_positions=last_five_positions,
            )
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
