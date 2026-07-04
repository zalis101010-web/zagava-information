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
    """Читает предыдущий status.json, если он есть, иначе возвращает пустой статус."""
    now = int(time.time())
    default = {
        "playing": False,
        "game": None,
        "started": now,
    }

    if not os.path.exists(STATUS_FILE):
        return default

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "playing": data.get("playing", False),
            "game": data.get("game"),
            "started": data.get("started") or now,
        }
    except (json.JSONDecodeError, OSError):
        return default


def fetch_steam_data(api_key, steam_id):
    """Делает запрос к Steam Web API и возвращает словарь player, либо None при ошибке."""
    url = API_URL.format(api_key=api_key, steam_id=steam_id)

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            raw = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"Ошибка запроса к Steam API: {e}", file=sys.stderr)
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора ответа Steam API: {e}", file=sys.stderr)
        return None

    players = data.get("response", {}).get("players", [])
    if not players:
        print("Steam API вернул пустой список игроков.", file=sys.stderr)
        return None

    return players[0]


def build_status(player, previous):
    """Строит новый статус на основе данных Steam и предыдущего состояния.

    Состояний всего два, у каждого свой таймер, который идёт с момента
    входа в это состояние и сбрасывается только при реальной смене:
      - playing=True, game="Имя игры"  -> "Играет в Имя игры | таймер"
      - playing=False, game=None       -> "Не играет | таймер"
    Офлайн и онлайн-без-игры на сайте выглядят одинаково ("Не играет"),
    но внутри всё равно отслеживаются как единое состояние.
    """
    now = int(time.time())

    if player is None:
        # Steam недоступен или произошла ошибка — сохраняем предыдущее
        # состояние, чтобы сайт не "моргал" и не ломался.
        return previous

    persona_state = player.get("personastate", 0)
    online = persona_state != 0
    current_game = player.get("gameextrainfo") if online else None
    playing = bool(current_game)

    same_state = (
        previous.get("playing") == playing
        and previous.get("game") == current_game
        and previous.get("started")
    )

    started = previous.get("started") if same_state else now

    return {
        "playing": playing,
        "game": current_game,
        "started": started,
    }


def main():
    api_key = os.environ.get("STEAM_API_KEY")
    steam_id = os.environ.get("STEAM_ID")

    previous = load_previous_status()

    if not api_key or not steam_id:
        print(
            "STEAM_API_KEY или STEAM_ID не заданы в переменных окружения. "
            "Оставляю status.json без изменений.",
            file=sys.stderr,
        )
        new_status = previous
    else:
        player = fetch_steam_data(api_key, steam_id)
        new_status = build_status(player, previous)

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_status, f, ensure_ascii=False, indent=4)
        f.write("\n")

    print("status.json обновлён:", json.dumps(new_status, ensure_ascii=False))


if __name__ == "__main__":
    main()
