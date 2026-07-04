let steamData = null;

function formatTime(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;

    return [
        h.toString().padStart(2, "0"),
        m.toString().padStart(2, "0"),
        s.toString().padStart(2, "0")
    ].join(":");
}

async function loadSteam() {
    try {

        const res = await fetch("status.json?t=" + Date.now());

        steamData = await res.json();

    } catch(e) {

        console.log(e);

    }
}

function renderSteam() {

    const el = document.getElementById("steamStatus");

    if (!steamData) {

        el.textContent = "Загрузка...";

        return;

    }

    if (!steamData.online) {

        el.textContent = "Не в сети";

        return;

    }

    if (!steamData.playing) {

        el.textContent = "В сети | Не играет";

        return;

    }

    const played = Math.floor(Date.now()/1000) - steamData.started;

    el.textContent =
        `Играет в ${steamData.game} | ${formatTime(played)}`;

}

loadSteam();

setInterval(loadSteam,40000);

setInterval(renderSteam,1000);