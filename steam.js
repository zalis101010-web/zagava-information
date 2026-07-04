(function () {
    "use strict";

    var STATUS_URL = "status.json";
    var FETCH_INTERVAL_MS = 40000; // раз в 40 секунд
    var TICK_INTERVAL_MS = 1000;   // раз в секунду

    var elementId = "steamStatus";
    var currentStatus = null; // последние данные из status.json
    var elapsedSeconds = 0;   // сколько секунд идёт текущая игра (локальный счётчик)

    function pad(num) {
        return String(num).padStart(2, "0");
    }

    function getMskHour() {
        // Та же логика, что и в часах на сайте: фиксированный МСК (UTC+3),
        // не зависит от часового пояса посетителя.
        var now = new Date();
        var msk = new Date(now.getTime() + now.getTimezoneOffset() * 60000 + 3 * 3600000);
        return msk.getHours();
    }

    function isSleepingHours() {
        var hour = getMskHour();
        return hour >= 0 && hour < 8; // с 00:00 до 08:00 по МСК
    }

    function formatDuration(totalSeconds) {
        if (totalSeconds < 0) {
            totalSeconds = 0;
        }
        var hours = Math.floor(totalSeconds / 3600);
        var minutes = Math.floor((totalSeconds % 3600) / 60);
        var seconds = Math.floor(totalSeconds % 60);
        return pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);
    }

    function render() {
        var el = document.getElementById(elementId);
        if (!el) {
            return;
        }

        if (!currentStatus) {
            el.textContent = "● Загрузка...";
            return;
        }

        if (!currentStatus.playing) {
            var label = isSleepingHours() ? "Спит" : "Не играет";
            el.textContent = "● " + label + " | " + formatDuration(elapsedSeconds);
            return;
        }

        var gameName = currentStatus.game || "Игра";
        el.textContent = "● Играет в " + gameName + " | " + formatDuration(elapsedSeconds);
    }

    function applyStatus(data) {
        var nowSeconds = Math.floor(Date.now() / 1000);

        if (data && data.started) {
            elapsedSeconds = nowSeconds - data.started;
            if (elapsedSeconds < 0) {
                elapsedSeconds = 0;
            }
        } else {
            elapsedSeconds = 0;
        }

        currentStatus = data;
        render();
    }

    function fetchStatus() {
        fetch(STATUS_URL + "?t=" + Date.now(), { cache: "no-store" })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Bad response: " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                applyStatus(data);
            })
            .catch(function (err) {
                // Steam или сеть недоступны — просто оставляем последнее
                // известное состояние на экране, сайт не ломаем.
                console.warn("Не удалось обновить Steam-статус:", err);
            });
    }

    function tick() {
        if (currentStatus) {
            elapsedSeconds += 1;
            render();
        }
    }

    function init() {
        render();
        fetchStatus();
        setInterval(fetchStatus, FETCH_INTERVAL_MS);
        setInterval(tick, TICK_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
