const LOCATIONS = {
  checkpoint: { label: "КПП", x: 15.5, y: 32, level: "floor1" },
  yard: { label: "Внутренний двор", x: 35, y: 28, level: "floor1" },
  hall: { label: "Главный холл", x: 52, y: 23, level: "floor1" },
  canteen: { label: "Столовая", x: 51, y: 38, level: "floor1" },
  archive: { label: "Архив", x: 69, y: 22, level: "floor1" },
  medbay: { label: "Медблок", x: 71, y: 38, level: "floor1" },
  lab: { label: "Лаборатория PX-17", x: 83, y: 14, level: "floor1" },
  server: { label: "Серверная", x: 58, y: 10, level: "floor1" },
  garage: { label: "Гараж", x: 30, y: 11, level: "floor1" },
  generator: { label: "Генераторная", x: 50, y: 61, level: "tech" },
  electrical: { label: "Электрощитовая", x: 21, y: 61, level: "tech" },
  storage: { label: "Склад химии", x: 78, y: 61, level: "tech" },
  vents: { label: "Вентиляция", x: 51, y: 76, level: "tech" },
  px17_storage: { label: "Хранилище PX-17", x: 49, y: 93, level: "underground" },
  test_chambers: { label: "Испытательные камеры", x: 21, y: 93, level: "underground" },
  central_lab: { label: "Центральная лаборатория", x: 78, y: 93, level: "underground" },
};

const MAP_LABELS = {
  floor1: "Этаж 1",
  tech: "Технический уровень",
  underground: "Подземный уровень",
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
      { id: "player", name: "Игрок", icon: "●", type: "player", loc: "central_lab", status: "перед выбором" },
      { id: "gleb", name: "Глеб", icon: "Г", type: "npc", loc: "central_lab", status: "истощён" },
      { id: "marina", name: "Марина", icon: "М", type: "npc", loc: "central_lab", status: "требует правду" },
      { id: "artem", name: "Артём", icon: "А", type: "npc", loc: "central_lab", status: "держит фото брата" },
      { id: "eva", name: "Ева", icon: "Е", type: "npc", loc: "central_lab", status: "боится утечки" },
    ],
  },
};

function getStateName() {
  const params = new URLSearchParams(window.location.search);
  return params.get("state") || localStorage.getItem("perimeter_map_state") || "day1_yard";
}

function getUnlockedMaps() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("maps") || localStorage.getItem("perimeter_unlocked_maps") || "";
  const unlocked = raw.split(",").map(x => x.trim()).filter(Boolean);
  if (unlocked.length) return new Set(unlocked);
  return new Set();
}

function setStateName(name) {
  localStorage.setItem("perimeter_map_state", name);
}

function setUnlockedMaps(maps) {
  localStorage.setItem("perimeter_unlocked_maps", [...maps].join(","));
}

function renderLevels(unlocked) {
  document.querySelectorAll(".level").forEach(level => {
    const id = level.dataset.level;
    level.classList.toggle("locked", !unlocked.has(id));
  });

  const list = document.getElementById("mapList");
  list.innerHTML = "";
  ["floor1", "tech", "underground"].forEach(id => {
    const item = document.createElement("div");
    item.className = `map-chip ${unlocked.has(id) ? "open" : "closed"}`;
    item.textContent = unlocked.has(id) ? `✓ ${MAP_LABELS[id]}` : `▣ ${MAP_LABELS[id]} — не найдено`;
    list.appendChild(item);
  });
}

function render(stateName) {
  const state = STATES[stateName] || STATES.day1_yard;
  const unlocked = getUnlockedMaps();
  setStateName(stateName);
  setUnlockedMaps(unlocked);

  document.getElementById("dayLabel").textContent = state.day;
  document.getElementById("timeLabel").textContent = state.time;
  renderLevels(unlocked);

  const layer = document.getElementById("markersLayer");
  layer.innerHTML = "";
  const offsets = {};

  for (const hero of state.heroes) {
    const loc = LOCATIONS[hero.loc];
    if (!loc || !unlocked.has(loc.level)) continue;
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

  const heroList = document.getElementById("heroList");
  heroList.innerHTML = "";
  state.heroes.forEach(hero => {
    const loc = LOCATIONS[hero.loc];
    const visible = loc && unlocked.has(loc.level);
    const card = document.createElement("div");
    card.className = "hero";
    const locText = visible ? `${loc.label} · ${hero.status}` : `локация скрыта · нужна карта уровня`;
    card.innerHTML = `<div class="avatar">${hero.icon}</div><div><strong>${hero.name}</strong><small>${locText}</small></div>`;
    heroList.appendChild(card);
  });
}

window.PerimeterMap = { render, STATES };
render(getStateName());
