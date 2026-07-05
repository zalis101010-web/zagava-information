(function () {
  const STATUS_URL = "status.json";
  const POLL_INTERVAL_MS = 40 * 1000;
  const TICK_INTERVAL_MS = 1000;

  const el = document.getElementById("steamStatus");
  if (!el) return;

  let currentStatus = null;
  let lastStarted = null;

  function formatDuration(totalSeconds) {
    const s = Math.max(0, Math.floor(totalSeconds));
    const hh = String(Math.floor(s / 3600)).padStart(2, "0");
    const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  }

  function render() {
    if (!currentStatus) {
      el.textContent = "Загрузка...";
      return;
    }

    const { online, playing, game, started } = currentStatus;

    if (!online) {
      el.textContent = "Не в сети";
      return;
    }

    if (playing && game) {
      const nowSec = Math.floor(Date.now() / 1000);

      if (!started || typeof started !== "number") {
        el.textContent = `Играет в ${game} | 00:00:00`;
        return;
      }

      const elapsed = nowSec - started;

      // 💥 защита от “вечного Dota”
      if (elapsed > 900) {
        el.textContent = "В сети | статус обновляется...";
        return;
      }

      el.textContent = `Играет в ${game} | ${formatDuration(elapsed)}`;
      return;
    }

    el.textContent = "В сети | Не играет";
  }

  async function fetchStatus() {
    try {
      const res = await fetch(STATUS_URL + "?v=" + Date.now(), {
        cache: "no-store",
      });

      const data = await res.json();
      currentStatus = data;

      if (data?.started !== lastStarted) {
        lastStarted = data.started;
        render();
      }
    } catch (e) {
      console.warn("status fetch error:", e);
    }

    render();
  }

  fetchStatus();
  setInterval(fetchStatus, POLL_INTERVAL_MS);
  setInterval(render, TICK_INTERVAL_MS);
})();
