import os
import asyncio
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Set

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAP_URL = os.getenv("MAP_URL", "https://wwgame28.github.io/perimeter/web_map/")
BASE_DIR = Path(__file__).resolve().parent
TEAM_IMAGE_B64 = BASE_DIR / "assets" / "team_intro.b64"

MAP_LABELS = {"floor1": "Этаж 1", "tech": "Технический уровень", "underground": "Подземный уровень"}
ITEM_LABELS = {"flashlight": "Фонарь", "tools": "Инструменты", "floor1_map": "Карта первого этажа", "tech_map": "Карта технического уровня", "underground_map": "Карта подземного уровня"}
DOC_LABELS = {"visitors_log": "Журнал посещений", "tech_scheme": "Схема кабельных тоннелей", "underground_file": "Папка: Подземный уровень. Доступ 4"}

WELCOME_TEXT = """╔════════════════════════════╗
        НИИ «ПЕРИМЕТР»
╚════════════════════════════╝

Интерактивная хоррор-история для Telegram.

Ты — участник первой вылазки в закрытый научный центр «Периметр». Объект официально заброшен после аварии 1990-х. По документам внутри нет людей. По рации — кто-то всё ещё зовёт на помощь.

В прошлом здесь изучали проект «Эхо» / PX-17 — вещество, которое усиливает память, вину, страх и голоса в темноте.

🟦 рациональный выбор — осторожность и анализ;
🟥 импульсивный выбор — риск и давление;
🟩 эмпатичный выбор — люди и доверие.

Нажми «🧑‍🚀 Знакомство с героями», чтобы увидеть команду, или «▶️ Начать вылазку», чтобы войти за ворота."""

HERO_INTRO_TEXT = """🧑‍🚀 Знакомство с героями

Перед тобой — первая вылазка в «Периметр». Все участники молоды, но у каждого уже есть причина бояться этого места.

● Игрок — главный герой без заданного лица. Его характер формируют твои решения.

Глеб Орлов, 29 — координатор. Держит команду в порядке, пока сам не начинает терять контроль.

Марина Соколова, 26 — инженер-спасатель. Пришла не просто на задание, а за ответом.

Артём Лучин, 24 — связист. Шутит, когда страшно. Слишком внимательно слушает рацию.

Ева Крайнова, 27 — врач. Замечает симптомы раньше, чем остальные признают, что что-то не так.

Фёдор — сторож КПП. Первый предупреждает: «Если услышишь знакомый голос — не отвечай».

Секреты персонажей не раскрываются заранее. Они появятся через сцены, документы и последствия решений."""

HELP_TEXT = """Команды:
/play — продолжить историю
/heroes — знакомство с героями
/map — карта
/inventory — инвентарь
/documents — документы
/status — статус
/restart — сначала"""

SCENES = {
    "start": {"title": "КПП-1. Ворота", "text": "Дождь стекает по бетонной арке КПП. За сеткой — чёрный двор, мёртвые окна и главный корпус НИИ «Периметр».\n\nФёдор говорит: «Если услышишь знакомый голос — не отвечай».\n\nЧто ты делаешь?", "choices": [("🟦 Расспросить Фёдора", "fedor"), ("🟥 Потребовать открыть ворота", "gate"), ("🟩 Предупредить команду", "team_scene")]},
    "fedor": {"title": "Фёдор", "text": "Фёдор протягивает тебе старый фонарь.\n\n🎒 Получен предмет: Фонарь.", "effects": {"add_item": "flashlight"}, "choices": [("Продолжить к воротам", "gate")]},
    "gate": {"title": "Точка невозврата", "text": "Ворота открываются. Металл скрипит так, будто комплекс просыпается. Позади ворота закрываются. Назад дороги уже нет.", "choices": [("🟦 Осмотреть двор", "yard"), ("🟥 Идти прямо в холл", "hall"), ("🟩 Проверить команду", "team_scene")]},
    "team_scene": {"title": "Команда", "text": "Глеб проверяет карту. Марина смотрит на крышу. Артём стучит пальцем по рации. Ева держит аптечку так крепко, будто уже знает, что она понадобится.", "choices": [("Продолжить ко входу", "gate")]},
    "yard": {"title": "Внутренний двор", "text": "Во дворе ржавые бочки, старый генератор и следы шин. Где-то внутри включается динамик: «Внимание... аварийный...» — и замолкает.", "choices": [("🟦 Проверить генератор", "generator"), ("🟥 Открыть гараж", "garage"), ("🟩 Позвать остальных в холл", "hall")]},
    "garage": {"title": "Гараж", "text": "На верстаке лежат фонарь, инструменты и лист с половиной схемы объекта.\n\n🎒 Получен предмет: Инструменты.", "effects": {"add_item": "tools"}, "choices": [("🟦 Забрать инструменты", "hall"), ("🟥 Открыть склад", "generator"), ("🟩 Вернуться к команде", "hall")]},
    "hall": {"title": "Главный холл", "text": "На стойке регистрации лежит журнал посещений. Под ним — схема: «ЭТАЖ 1. СЛУЖЕБНЫЙ ПЛАН».\n\n🗺 Найдена карта первого этажа.\n📄 Найден документ: Журнал посещений.", "effects": {"unlock_map": "floor1", "add_item": "floor1_map", "add_doc": "visitors_log"}, "choices": [("🟦 Открыть карту", "map_hint"), ("🟥 Идти в архив", "archive"), ("🟩 Собрать команду", "canteen")]},
    "map_hint": {"title": "Служебный план", "text": "На карте отмечены КПП, двор, гараж, медпункт, холл, архив, серверная и лаборатории. Теперь доступна кнопка «🗺 Карта».", "choices": [("Продолжить в архив", "archive")]},
    "archive": {"title": "Архив", "text": "В папке «Служебные коммуникации» лежит схема тоннелей и генераторной.\n\n🗺 Найдена карта технического уровня.\n📄 Найден документ: Схема кабельных тоннелей.", "effects": {"unlock_map": "tech", "add_item": "tech_map", "add_doc": "tech_scheme"}, "choices": [("🟦 Изучить схему", "generator"), ("🟥 Спуститься вниз", "underground_map"), ("🟩 Вернуться в столовую", "canteen")]},
    "generator": {"title": "Генераторная", "text": "Генераторная дрожит от низкого гула. На стене — схема вентиляции и электрощитовой.\n\n🗺 Открыт технический уровень.", "effects": {"unlock_map": "tech", "add_item": "tech_map"}, "choices": [("🟦 Отключить часть питания", "underground_map"), ("🟥 Идти дальше по тоннелю", "underground_map"), ("🟩 Вернуться к остальным", "canteen")]},
    "underground_map": {"title": "Доступ 4", "text": "За технической дверью лежит папка: «ПОДЗЕМНЫЙ УРОВЕНЬ. ДОСТУП 4».\n\n🗺 Найдена карта подземного уровня.\n📄 Найден документ: Папка подземного уровня.", "effects": {"unlock_map": "underground", "add_item": "underground_map", "add_doc": "underground_file"}, "choices": [("🟦 Открыть карту", "final_lab"), ("🟥 Идти в хранилище PX-17", "final_lab"), ("🟩 Позвать команду", "canteen")]},
    "canteen": {"title": "Столовая", "text": "Столовая становится временным лагерем. На столе лежат карты, документы и фонари.", "choices": [("Продолжить", "final_lab")]},
    "final_lab": {"title": "Центральная лаборатория", "text": "Все найденные карты сходятся в одной точке: центральная лаборатория PX-17. Дальше будет не вопрос пути. Дальше будет вопрос выбора.", "choices": [("🔄 Начать заново", "start")]},
}

SCENE_TO_MAP_STATE = {"start": "day1_start", "fedor": "day1_start", "gate": "day1_start", "team_scene": "day1_start", "yard": "day1_yard", "garage": "day1_yard", "hall": "day1_yard", "map_hint": "day1_yard", "archive": "day1_yard", "generator": "day1_yard", "underground_map": "day2_missing", "canteen": "day2_missing", "final_lab": "day3_final"}

@dataclass
class PlayerState:
    scene: str = "start"
    maps: Set[str] = field(default_factory=set)
    items: Set[str] = field(default_factory=set)
    docs: Set[str] = field(default_factory=set)

players: Dict[int, PlayerState] = {}

def get_player(user_id: int) -> PlayerState:
    players.setdefault(user_id, PlayerState())
    return players[user_id]

def reset_player(user_id: int):
    players[user_id] = PlayerState()

def apply_effects(p: PlayerState, scene_id: str) -> list[str]:
    e = SCENES.get(scene_id, {}).get("effects", {})
    out = []
    if e.get("unlock_map") and e["unlock_map"] not in p.maps:
        p.maps.add(e["unlock_map"]); out.append(f"🗺 Открыта карта: {MAP_LABELS[e['unlock_map']]}")
    if e.get("add_item") and e["add_item"] not in p.items:
        p.items.add(e["add_item"]); out.append(f"🎒 Добавлено: {ITEM_LABELS[e['add_item']]}")
    if e.get("add_doc") and e["add_doc"] not in p.docs:
        p.docs.add(e["add_doc"]); out.append(f"📄 Добавлено: {DOC_LABELS[e['add_doc']]}")
    return out

def menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="▶️ Начать вылазку"), KeyboardButton(text="🧑‍🚀 Знакомство с героями")],
        [KeyboardButton(text="🗺 Карта"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="📄 Документы"), KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="📜 Помощь"), KeyboardButton(text="🔄 Сначала")],
    ], resize_keyboard=True)

def map_url(scene: str, maps: Set[str]) -> str:
    state = SCENE_TO_MAP_STATE.get(scene, "day1_yard")
    opened = ",".join(x for x in ["floor1", "tech", "underground"] if x in maps)
    return f"{MAP_URL}?state={state}&maps={opened}"

def scene_buttons(scene: str, p: PlayerState) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t, callback_data=f"go:{n}")] for t, n in SCENES[scene]["choices"]]
    rows.append([InlineKeyboardButton(text="🧑‍🚀 Герои", callback_data="heroes")])
    if p.maps:
        rows.append([InlineKeyboardButton(text="🗺 Мини-карта", url=map_url(scene, p.maps))])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def team_image():
    if not TEAM_IMAGE_B64.exists():
        return None
    raw = TEAM_IMAGE_B64.read_text(encoding="utf-8").strip()
    if not raw or raw == "PLACEHOLDER":
        return None
    return BufferedInputFile(base64.b64decode(raw), filename="perimeter_team.jpg")

async def send_heroes(obj):
    img = team_image()
    if isinstance(obj, CallbackQuery):
        if img:
            await obj.message.answer_photo(img, caption="Команда первой вылазки. Главный герой — чёрный силуэт в центре.")
        await obj.message.answer(HERO_INTRO_TEXT)
    else:
        if img:
            await obj.answer_photo(img, caption="Команда первой вылазки. Главный герой — чёрный силуэт в центре.")
        await obj.answer(HERO_INTRO_TEXT, reply_markup=menu())

async def send_scene(obj, user_id: int, scene_id: str):
    p = get_player(user_id); p.scene = scene_id
    notes = apply_effects(p, scene_id)
    s = SCENES[scene_id]
    text = f"▌ {s['title']}\n\n{s['text']}" + ("\n\n" + "\n".join(notes) if notes else "")
    if isinstance(obj, CallbackQuery):
        await obj.message.answer(text, reply_markup=scene_buttons(scene_id, p))
    else:
        await obj.answer(text, reply_markup=scene_buttons(scene_id, p))

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(m: types.Message):
        get_player(m.from_user.id)
        await m.answer(WELCOME_TEXT, reply_markup=menu())

    @dp.message(Command("play"))
    @dp.message(F.text == "▶️ Начать вылазку")
    async def play(m: types.Message):
        await send_scene(m, m.from_user.id, get_player(m.from_user.id).scene)

    @dp.message(Command("heroes"))
    @dp.message(F.text == "🧑‍🚀 Знакомство с героями")
    async def heroes(m: types.Message):
        await send_heroes(m)

    @dp.message(Command("map"))
    @dp.message(F.text == "🗺 Карта")
    async def show_map(m: types.Message):
        p = get_player(m.from_user.id)
        if not p.maps:
            await m.answer("🗺 Карта недоступна. Найди схему на локации.")
        else:
            rows = [[InlineKeyboardButton(text="🗺 Открыть мини-карту", url=map_url(p.scene, p.maps))]]
            await m.answer("Открытые карты:\n" + "\n".join(MAP_LABELS[x] for x in p.maps), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

    @dp.message(Command("inventory"))
    @dp.message(F.text == "🎒 Инвентарь")
    async def inv(m: types.Message):
        p = get_player(m.from_user.id)
        await m.answer("🎒 Инвентарь:\n" + ("\n".join(ITEM_LABELS[x] for x in p.items) if p.items else "пусто"))

    @dp.message(Command("documents"))
    @dp.message(F.text == "📄 Документы")
    async def docs(m: types.Message):
        p = get_player(m.from_user.id)
        await m.answer("📄 Документы:\n" + ("\n".join(DOC_LABELS[x] for x in p.docs) if p.docs else "не найдены"))

    @dp.message(Command("status"))
    @dp.message(F.text == "📊 Статус")
    async def status(m: types.Message):
        p = get_player(m.from_user.id)
        await m.answer(f"📊 Статус\nСцена: {SCENES[p.scene]['title']}\nКарт: {len(p.maps)}/3\nПредметов: {len(p.items)}\nДокументов: {len(p.docs)}")

    @dp.message(Command("restart"))
    @dp.message(F.text == "🔄 Сначала")
    async def restart(m: types.Message):
        reset_player(m.from_user.id)
        await m.answer("Прогресс сброшен.", reply_markup=menu())
        await send_scene(m, m.from_user.id, "start")

    @dp.message(Command("help"))
    @dp.message(F.text == "📜 Помощь")
    async def help_cmd(m: types.Message):
        await m.answer(HELP_TEXT, reply_markup=menu())

    @dp.callback_query(lambda c: c.data.startswith("go:"))
    async def go(c: CallbackQuery):
        await c.answer()
        await send_scene(c, c.from_user.id, c.data.split(":", 1)[1])

    @dp.callback_query(lambda c: c.data == "heroes")
    async def heroes_cb(c: CallbackQuery):
        await c.answer()
        await send_heroes(c)

    @dp.message()
    async def fallback(m: types.Message):
        await m.answer("Используй кнопки меню или /help.", reply_markup=menu())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
