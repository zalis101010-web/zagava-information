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


def load_previous_status():
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
    except Exception:
        return default


def fetch_steam_data(api_key, steam_id):
    url = API_URL.format(api_key=api_key, steam_id=steam_id)

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Steam API error: {e}", file=sys.stderr)
        return None


def build_status(player, previous):
    now = int(time.time())

    # ❗ если Steam не ответил — НЕ ломаем текущее состояние
    if not player:
        return previous

    persona_state = player.get("personastate", 0)
    online = persona_state != 0

    game = player.get("gameextrainfo") if online else None
    playing = game is not None

    prev_game = previous.get("game")
    prev_playing = previous.get("playing")

    # 💥 ключевая логика: смена игры или выход
    game_changed = game != prev_game

    if playing:
        # старт новой сессии только если игра реально изменилась
        started = previous.get("started")

        if not prev_playing or game_changed:
            started = now

    else:
        # 💥 ВАЖНО: всегда сбрасываем при выходе
        started = None

    return {
        "online": online,
        "playing": playing,
        "game": game,
        "started": started,
    }


def main():
    api_key = os.environ.get("STEAM_API_KEY")
    steam_id = os.environ.get("STEAM_ID")

    previous = load_previous_status()

    if not api_key or not steam_id:
        print("Missing STEAM_API_KEY or STEAM_ID", file=sys.stderr)
        new_status = previous
    else:
        data = fetch_steam_data(api_key, steam_id)
        player = data.get("response", {}).get("players", [None])[0] if data else None
        new_status = build_status(player, previous)

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_status, f, ensure_ascii=False, indent=4)
        f.write("\n")

    print("Updated:", new_status)


if __name__ == "__main__":
    main()
