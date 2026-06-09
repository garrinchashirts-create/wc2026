"""
Fetches WC 2026 odds from The Odds API and saves to odds_data.json
Runs daily via GitHub Actions
"""
import urllib.request
import json
import os
from datetime import datetime, timezone

API_KEY = os.environ.get("ODDS_API_KEY", "b3e388351ca7131ebb5a045ee7f5e4c8")
BASE_URL = "https://api.the-odds-api.com/v4"

# Sport keys to try for WC 2026
SPORT_KEYS = [
    "soccer_fifa_world_cup",
    "soccer_fifa_world_cup_2026",
    "soccer_world_cup",
]

MARKETS = "h2h,totals,btts"
REGIONS = "eu,uk"
ODDS_FORMAT = "decimal"

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_available_sports():
    url = f"{BASE_URL}/sports?apiKey={API_KEY}"
    data = fetch(url)
    if not data:
        return []
    soccer = [s for s in data if "soccer" in s.get("group","").lower() or "football" in s.get("group","").lower()]
    return soccer

def get_odds(sport_key):
    url = (f"{BASE_URL}/sports/{sport_key}/odds"
           f"?apiKey={API_KEY}"
           f"&regions={REGIONS}"
           f"&markets={MARKETS}"
           f"&oddsFormat={ODDS_FORMAT}"
           f"&dateFormat=iso")
    return fetch(url)

def main():
    print(f"Fetching odds at {datetime.now(timezone.utc).isoformat()}")

    # Try to find WC 2026 sport key
    sports = get_available_sports()
    wc_sports = [s for s in sports if "world" in s.get("title","").lower() or "world" in s.get("key","").lower()]
    print(f"Available WC sports: {[s['key'] for s in wc_sports]}")

    all_games = []
    sport_key_used = None

    # Try known keys first
    for key in SPORT_KEYS:
        data = get_odds(key)
        if data and isinstance(data, list) and len(data) > 0:
            all_games = data
            sport_key_used = key
            print(f"Got {len(data)} games from key: {key}")
            break

    # Fall back to discovered keys
    if not all_games:
        for sport in wc_sports:
            data = get_odds(sport["key"])
            if data and isinstance(data, list) and len(data) > 0:
                all_games = data
                sport_key_used = sport["key"]
                print(f"Got {len(data)} games from discovered key: {sport['key']}")
                break

    # Structure output
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sport_key": sport_key_used,
        "available_wc_sports": [s["key"] for s in wc_sports],
        "games_count": len(all_games),
        "games": []
    }

    for game in all_games:
        home = game.get("home_team","")
        away = game.get("away_team","")
        commence = game.get("commence_time","")

        # Extract best odds per outcome
        best_odds = {}
        all_bookmaker_odds = []

        for bm in game.get("bookmakers", []):
            for market in bm.get("markets", []):
                mkey = market.get("key","")
                for outcome in market.get("outcomes", []):
                    oname = outcome.get("name","")
                    oprice = outcome.get("price", 0)
                    okey = f"{mkey}_{oname}"
                    all_bookmaker_odds.append({
                        "bookmaker": bm.get("title",""),
                        "market": mkey,
                        "outcome": oname,
                        "price": oprice
                    })
                    if okey not in best_odds or oprice > best_odds[okey]["price"]:
                        best_odds[okey] = {"market": mkey, "outcome": oname, "price": oprice, "bookmaker": bm.get("title","")}

        # Build clean odds structure
        h2h = {}
        totals = {}
        btts_yes = None

        for key, odd in best_odds.items():
            m = odd["market"]
            o = odd["outcome"]
            p = odd["price"]
            if m == "h2h":
                if o == home: h2h["home"] = p
                elif o == away: h2h["away"] = p
                elif o == "Draw": h2h["draw"] = p
            elif m == "totals":
                if "Over" in o: totals["over25"] = p
                elif "Under" in o: totals["under25"] = p
            elif m == "btts":
                if o == "Yes": btts_yes = p

        output["games"].append({
            "id": game.get("id",""),
            "home_team": home,
            "away_team": away,
            "commence_time": commence,
            "h2h": h2h,
            "totals": totals,
            "btts_yes": btts_yes,
            "bookmakers_count": len(game.get("bookmakers",[]))
        })

    # Save
    with open("odds_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(output['games'])} games to odds_data.json")
    print(f"Updated at: {output['updated_at']}")

if __name__ == "__main__":
    main()
