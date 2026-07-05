import json
import os
import sys
import time
import urllib.request
import urllib.error

STATUS_FILE = "status.json"

API_URL = (
    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    "?key={api_key}&steamids={steam_id}"
)


def load_previous():
    default = {
        "online": False,
        "playing": False,
        "game": None,
        "started": None,
    }

    if not os.path.exists(STATUS_FILE):
        return default

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def fetch(api_key, steam_id):
    url = API_URL.format(api_key=api_key, steam_id=steam_id)

    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Steam API error:", e, file=sys.stderr)
        return None


def build_status(player, prev):
    now = int(time.time())

    # 💥 если Steam не ответил — НЕ держим старое состояние
    if not player:
        return {
            "online": prev.get("online", False),
            "playing": False,
            "game": None,
            "started": None,
        }

    persona = player.get("personastate", 0)
    online = persona != 0

    game = player.get("gameextrainfo") if online else None
    playing = game is not None

    prev_game = prev.get("game")
    prev_started = prev.get("started")

    # 💥 если игра поменялась → новый старт
    game_changed = game != prev_game

    if not playing:
        return {
            "online": online,
            "playing": False,
            "game": None,
            "started": None,
        }

    if game_changed or not prev_started:
        started = now
    else:
        started = prev_started

    return {
        "online": online,
        "playing": playing,
        "game": game,
        "started": started,
    }


def main():
    api_key = os.environ.get("STEAM_API_KEY")
    steam_id = os.environ.get("STEAM_ID")

    prev = load_previous()

    if not api_key or not steam_id:
        print("Missing env vars", file=sys.stderr)
        new_status = prev
    else:
        data = fetch(api_key, steam_id)
        player = data.get("response", {}).get("players", [None])[0] if data else None
        new_status = build_status(player, prev)

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_status, f, ensure_ascii=False, indent=2)

    print("Updated:", new_status)


if __name__ == "__main__":
    main()
