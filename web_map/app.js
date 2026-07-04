const LOCATIONS = {
  checkpoint: { label: "КПП", x: 15.5, y: 76 },
  yard: { label: "Внутренний двор", x: 35, y: 65 },
  hall: { label: "Главный холл", x: 52, y: 56 },
  canteen: { label: "Столовая", x: 51, y: 80 },
  archive: { label: "Архив", x: 69, y: 54 },
  medbay: { label: "Медблок", x: 71, y: 76 },
  lab: { label: "Лаборатория PX-17", x: 83, y: 39 },
  underground: { label: "Нижний уровень", x: 79, y: 20 },
  server: { label: "Серверная", x: 58, y: 30 },
  garage: { label: "Гараж", x: 30, y: 40 },
};

const STATES = {
  day1_start: {
    day: "День 1",
    time: "07:50",
    heroes: [
      { id: "player", name: "Игрок", icon: "●", type: "player", loc: "checkpoint", status: "у ворот" },
      { id: "gleb", name: "Глеб", icon: "Г", type: "npc", loc: "checkpoint", status: "держит план" },
      { id: "marina", name: "Марина", icon: "М", type: "npc", loc: "checkpoint", status: "осматривает периметр" },
      { id: "artem", name: "Артём", icon: "А", type: "npc", loc: "checkpoint", status: "проверяет рацию" },
      { id: "eva", name: "Ева", icon: "Е", type: "npc", loc: "checkpoint", status: "молчит" },
    ],
  },
  day1_yard: {
    day: "День 1",
    time: "08:10",
    heroes: [
      { id: "player", name: "Игрок", icon: "●", type: "player", loc: "yard", status: "выбирает маршрут" },
      { id: "gleb", name: "Глеб", icon: "Г", type: "npc", loc: "hall", status: "ждёт у входа" },
      { id: "marina", name: "Марина", icon: "М", type: "npc", loc: "yard", status: "у генератора" },
      { id: "artem", name: "Артём", icon: "А", type: "npc", loc: "garage", status: "ищет инструменты" },
      { id: "eva", name: "Ева", icon: "Е", type: "npc", loc: "medbay", status: "проверяет дверь" },
    ],
  },
  day2_missing: {
    day: "День 2",
    time: "07:15",
    heroes: [
      { id: "player", name: "Игрок", icon: "●", type: "player", loc: "canteen", status: "проснулся" },
      { id: "gleb", name: "Глеб", icon: "Г", type: "missing", loc: "lab", status: "местоположение неизвестно" },
      { id: "marina", name: "Марина", icon: "М", type: "npc", loc: "canteen", status: "злится" },
      { id: "artem", name: "Артём", icon: "А", type: "npc", loc: "canteen", status: "слушает рацию" },
      { id: "eva", name: "Ева", icon: "Е", type: "npc", loc: "canteen", status: "собирает аптечку" },
    ],
  },
  day3_final: {
    day: "День 3",
    time: "21:40",
    heroes: [
      { id: "player", name: "Игрок", icon: "●", type: "player", loc: "lab", status: "перед выбором" },
      { id: "gleb", name: "Глеб", icon: "Г", type: "npc", loc: "lab", status: "истощён" },
      { id: "marina", name: "Марина", icon: "М", type: "npc", loc: "lab", status: "требует правду" },
      { id: "artem", name: "Артём", icon: "А", type: "npc", loc: "lab", status: "держит фото брата" },
      { id: "eva", name: "Ева", icon: "Е", type: "npc", loc: "lab", status: "боится утечки" },
    ],
  },
};

function getStateName() {
  const params = new URLSearchParams(window.location.search);
  return params.get("state") || localStorage.getItem("perimeter_map_state") || "day1_yard";
}

function setStateName(name) {
  localStorage.setItem("perimeter_map_state", name);
}

function render(stateName) {
  const state = STATES[stateName] || STATES.day1_yard;
  setStateName(stateName);
  document.getElementById("dayLabel").textContent = state.day;
  document.getElementById("timeLabel").textContent = state.time;

  const layer = document.getElementById("markersLayer");
  layer.innerHTML = "";
  const offsets = {};

  for (const hero of state.heroes) {
    const loc = LOCATIONS[hero.loc];
    if (!loc) continue;
    offsets[hero.loc] = (offsets[hero.loc] || 0) + 1;
    const n = offsets[hero.loc];
    const marker = document.createElement("div");
    marker.className = `marker ${hero.type}`;
    marker.textContent = hero.icon;
    marker.title = `${hero.name} — ${hero.status}`;
    marker.style.left = `calc(${loc.x}% + ${(n - 1) * 18}px)`;
    marker.style.top = `calc(${loc.y}% + ${(n - 1) * 12}px)`;
    layer.appendChild(marker);
  }

  const list = document.getElementById("heroList");
  list.innerHTML = "";
  state.heroes.forEach(hero => {
    const loc = LOCATIONS[hero.loc]?.label || "неизвестно";
    const card = document.createElement("div");
    card.className = "hero";
    card.innerHTML = `<div class="avatar">${hero.icon}</div><div><strong>${hero.name}</strong><small>${loc} · ${hero.status}</small></div>`;
    list.appendChild(card);
  });
}

window.PerimeterMap = { render, STATES };
render(getStateName());
