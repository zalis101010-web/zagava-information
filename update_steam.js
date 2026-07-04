const fs = require("fs");

const API_KEY = process.env.STEAM_API_KEY;
const STEAM_ID = "76561199789113509";

async function main() {

    let old = {
        online: false,
        playing: false,
        game: "",
        started: 0
    };

    if (fs.existsSync("status.json")) {
        old = JSON.parse(fs.readFileSync("status.json", "utf8"));
    }

    const url =
        `https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=${API_KEY}&steamids=${STEAM_ID}`;

    const res = await fetch(url);

    const json = await res.json();

    const p = json.response.players[0];

    const online = p.personastate !== 0;

    const playing = !!p.gameextrainfo;

    const game = p.gameextrainfo || "";

    let started = old.started;

    if (playing) {

        if (old.game !== game) {

            started = Math.floor(Date.now()/1000);

        }

    } else {

        started = 0;

    }

    const result = {

        online,

        playing,

        game,

        started

    };

    fs.writeFileSync(
        "status.json",
        JSON.stringify(result,null,2)
    );

}

main();
