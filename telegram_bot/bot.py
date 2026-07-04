import os
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Set, List, Tuple, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAP_URL = os.getenv("MAP_URL", "https://wwgame28.github.io/perimeter/web_map/")

MAP_LABELS = {
    "floor1": "Этаж 1",
    "tech": "Технический уровень",
    "underground": "Подземный уровень",
}

ITEM_LABELS = {
    "flashlight": "Фонарь",
    "tools": "Инструменты",
    "floor1_map": "Карта первого этажа",
    "tech_map": "Карта технического уровня",
    "underground_map": "Карта подземного уровня",
}

DOC_LABELS = {
    "visitors_log": "Журнал посещений",
    "tech_scheme": "Схема кабельных тоннелей",
    "underground_file": "Папка: Подземный уровень. Доступ 4",
}

WELCOME_TEXT = """╔════════════════════════════╗
        НИИ «ПЕРИМЕТР»
╚════════════════════════════╝

Интерактивная хоррор-история для Telegram.

Ты — участник первой вылазки в закрытый научный центр «Периметр». Объект официально заброшен после аварии 1990-х. По документам внутри нет людей. По рации — кто-то всё ещё зовёт на помощь.

В прошлом здесь изучали проект «Эхо» / PX-17 — вещество, которое не создаёт чудовищ напрямую. Оно делает страшнее другое: память, вину, голоса, знакомые лица в темноте.

Правила простые:
🟦 рациональный выбор — осторожность и анализ;
🟥 импульсивный выбор — риск и давление;
🟩 эмпатичный выбор — люди и доверие.

Каждый выбор меняет маршрут, отношения, найденные предметы, карты и финал.

Нажми «▶️ Начать вылазку», чтобы войти за ворота."""

HELP_TEXT = """Команды и кнопки:

▶️ Начать вылазку — начать или продолжить историю.
🗺 Карта — открыть найденные уровни комплекса.
🎒 Инвентарь — найденные предметы.
📄 Документы — найденные записи и улики.
👥 Команда — краткое описание героев.
📊 Статус — текущее состояние прохождения.
🔄 Сначала — сбросить прогресс.

Карта открывается не сразу. Сначала нужно найти схемы на локациях."""

TEAM_TEXT = """👥 Команда вылазки

● Игрок — главный герой без заданного лица. Его характер формируют решения.

Глеб Орлов, 29 — координатор. Держит всё под контролем, пока контроль не начинает трещать.

Марина Соколова, 26 — инженер-спасатель. Привыкла действовать жёстко и не доверяет фонду.

Артём Лучин, 24 — связист. Шутит, когда страшно. Слишком внимательно слушает рацию.

Ева Крайнова, 27 — врач. Смотрит на комплекс так, будто уже знает, чем пахнет беда.

Фёдор — сторож КПП. Первый человек, который говорит: «Если услышишь знакомый голос — не отвечай»."""

SCENES = {
    "start": {
        "title": "КПП-1. Ворота",
        "text": "Дождь стекает по бетонной арке КПП. За сеткой — чёрный двор, мёртвые окна и главный корпус НИИ «Периметр».\n\nФёдор, сторож КПП, не смотрит тебе в глаза. Он только сжимает связку ключей и говорит:\n\n«Если услышишь знакомый голос — не отвечай. Даже если он будет просить помощи».\n\nЧто ты делаешь?",
        "choices": [
            ("🟦 Расспросить Фёдора", "fedor"),
            ("🟥 Потребовать открыть ворота", "gate"),
            ("🟩 Предупредить команду", "team_scene"),
        ],
    },
    "fedor": {
        "title": "Фёдор",
        "text": "Фёдор долго молчит. Дым от сигареты расползается между вами, как туман.\n\n«Ночью здесь зовут голосами умерших. Я не знаю, что это. Но отвечать нельзя».\n\nОн протягивает тебе старый фонарь. Пластик липкий от влаги, линза мутная, но лампа ещё живая.\n\n🎒 Получен предмет: Фонарь.",
        "effects": {"add_item": "flashlight"},
        "choices": [("Продолжить к воротам", "gate")],
    },
    "gate": {
        "title": "Точка невозврата",
        "text": "Ворота медленно открываются. Металл скрипит так низко, будто внутри комплекса просыпается огромная машина.\n\nГлеб первым переступает линию КПП. Марина проверяет замок. Артём пытается пошутить, но не заканчивает фразу. Ева молча смотрит на окна второго этажа.\n\nПозади ворота закрываются. Назад дороги уже нет.",
        "choices": [
            ("🟦 Осмотреть двор", "yard"),
            ("🟥 Идти прямо в холл", "hall"),
            ("🟩 Проверить команду", "team_scene"),
        ],
    },
    "team_scene": {
        "title": "Команда",
        "text": "Глеб разворачивает план объекта. Марина смотрит на крышу, где мигает красная лампа. Артём стучит пальцем по рации. Ева держит аптечку так крепко, будто уже знает, что она понадобится.\n\nНа секунду все кажутся обычными людьми. Молодыми. Уставшими. Живыми.\n\nИ именно поэтому это место становится страшнее.",
        "choices": [("Продолжить ко входу", "gate")],
    },
    "yard": {
        "title": "Внутренний двор",
        "text": "Во дворе ржавые бочки, старый генератор и следы шин. Лужи отражают красные огни антенн на крыше.\n\nГде-то внутри комплекса коротко включается динамик: «Внимание... аварийный...» — и замолкает.\n\nМарина показывает на гараж. Артём — на боковую дверь. Глеб — на главный вход.",
        "choices": [
            ("🟦 Проверить генератор", "generator"),
            ("🟥 Открыть гараж", "garage"),
            ("🟩 Позвать остальных в холл", "hall"),
        ],
    },
    "garage": {
        "title": "Гараж",
        "text": "В гараже пахнет бензином, мокрым металлом и старой резиной. На верстаке лежат фонарь, набор инструментов и лист с половиной схемы объекта.\n\nЭто не карта, но она подтверждает главное: под зданием есть технический уровень.\n\n🎒 Получен предмет: Инструменты.",
        "effects": {"add_item": "tools"},
        "choices": [
            ("🟦 Забрать инструменты", "hall"),
            ("🟥 Открыть склад", "generator"),
            ("🟩 Вернуться к команде", "hall"),
        ],
    },
    "hall": {
        "title": "Главный холл",
        "text": "Холл пуст. Часы на стене остановились на 03:07. На стойке регистрации лежит журнал посещений.\n\nПод ним — сложенная бумажная схема: «ЭТАЖ 1. СЛУЖЕБНЫЙ ПЛАН». Чернила расплылись от влаги, но основные зоны читаются.\n\n🗺 Найдена карта первого этажа.\n📄 Найден документ: Журнал посещений.",
        "effects": {"unlock_map": "floor1", "add_item": "floor1_map", "add_doc": "visitors_log"},
        "choices": [
            ("🟦 Открыть карту", "map_hint"),
            ("🟥 Идти в архив", "archive"),
            ("🟩 Собрать команду", "canteen"),
        ],
    },
    "map_hint": {
        "title": "Служебный план",
        "text": "Ты разворачиваешь бумагу на стойке. На схеме отмечены КПП, внутренний двор, гараж, медпункт, холл, архив, серверная и лаборатории.\n\nТеперь команда может пользоваться мини-картой через кнопку «🗺 Карта» или команду /map.",
        "choices": [("Продолжить в архив", "archive")],
    },
    "archive": {
        "title": "Архив",
        "text": "В архиве пахнет пылью и растворителем. Шкафы стоят рядами, будто стены внутри стен.\n\nВ папке «Служебные коммуникации» лежит схема кабельных тоннелей и генераторной. На полях — чужие пометки красным карандашом: «НЕ ВКЛЮЧАТЬ ВЕНТИЛЯЦИЮ ПРИ УТЕЧКЕ».\n\n🗺 Найдена карта технического уровня.\n📄 Найден документ: Схема кабельных тоннелей.",
        "effects": {"unlock_map": "tech", "add_item": "tech_map", "add_doc": "tech_scheme"},
        "choices": [
            ("🟦 Изучить схему", "generator"),
            ("🟥 Спуститься вниз", "underground_map"),
            ("🟩 Вернуться в столовую", "canteen"),
        ],
    },
    "generator": {
        "title": "Генераторная",
        "text": "Генераторная дрожит от низкого гула. На стене висит служебный щит с пометками вентиляции, электрощитовой и химического склада.\n\nТеперь понятно, как технический уровень связан с распространением PX-17. Если ошибиться с питанием, комплекс может стать ловушкой.",
        "effects": {"unlock_map": "tech", "add_item": "tech_map"},
        "choices": [
            ("🟦 Отключить часть питания", "underground_map"),
            ("🟥 Идти дальше по тоннелю", "underground_map"),
            ("🟩 Вернуться к остальным", "canteen"),
        ],
    },
    "underground_map": {
        "title": "Доступ 4",
        "text": "За технической дверью обнаружена старая папка с красной печатью: «ПОДЗЕМНЫЙ УРОВЕНЬ. ДОСТУП 4».\n\nБумага влажная, но на ней видны испытательные камеры, хранилище PX-17 и центральная лаборатория.\n\n🗺 Найдена карта подземного уровня.\n📄 Найден документ: Папка подземного уровня.",
        "effects": {"unlock_map": "underground", "add_item": "underground_map", "add_doc": "underground_file"},
        "choices": [
            ("🟦 Открыть карту", "final_lab"),
            ("🟥 Идти в хранилище PX-17", "final_lab"),
            ("🟩 Позвать команду", "canteen"),
        ],
    },
    "canteen": {
        "title": "Столовая",
        "text": "Столовая становится временным лагерем. На столе лежат найденные карты, документы и фонари.\n\nТеперь объект больше не кажется непонятным лабиринтом. Но от этого он не стал безопаснее. Наоборот: когда ты видишь всю схему, становится ясно, как глубоко вы уже внутри.",
        "choices": [("Продолжить", "final_lab")],
    },
    "final_lab": {
        "title": "Центральная лаборатория",
        "text": "Все найденные карты сходятся в одной точке: центральная лаборатория PX-17.\n\nИменно туда ведут маршруты, следы и чужие записи. Дальше будет не вопрос пути. Дальше будет вопрос выбора.",
        "choices": [("🔄 Начать заново", "start")],
    },
}

SCENE_TO_MAP_STATE = {
    "start": "day1_start",
    "fedor": "day1_start",
    "gate": "day1_start",
    "team_scene": "day1_start",
    "yard": "day1_yard",
    "garage": "day1_yard",
    "hall": "day1_yard",
    "map_hint": "day1_yard",
    "archive": "day1_yard",
    "generator": "day1_yard",
    "underground_map": "day2_missing",
    "canteen": "day2_missing",
    "final_lab": "day3_final",
}

@dataclass
class PlayerState:
    scene: str = "start"
    maps: Set[str] = field(default_factory=set)
    items: Set[str] = field(default_factory=set)
    docs: Set[str] = field(default_factory=set)

players: Dict[int, PlayerState] = {}

def get_player(user_id: int) -> PlayerState:
    if user_id not in players:
        players[user_id] = PlayerState()
    return players[user_id]

def reset_player(user_id: int) -> PlayerState:
    players[user_id] = PlayerState()
    return players[user_id]

def apply_effects(player: PlayerState, scene_id: str) -> List[str]:
    scene = SCENES.get(scene_id, {})
    effects = scene.get("effects", {})
    notices: List[str] = []

    if "unlock_map" in effects:
        map_id = effects["unlock_map"]
        if map_id not in player.maps:
            player.maps.add(map_id)
            notices.append(f"🗺 Открыта карта: {MAP_LABELS[map_id]}")

    if "add_item" in effects:
        item_id = effects["add_item"]
        if item_id not in player.items:
            player.items.add(item_id)
            notices.append(f"🎒 В инвентарь добавлено: {ITEM_LABELS[item_id]}")

    if "add_doc" in effects:
        doc_id = effects["add_doc"]
        if doc_id not in player.docs:
            player.docs.add(doc_id)
            notices.append(f"📄 В журнал добавлено: {DOC_LABELS[doc_id]}")

    return notices

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ Начать вылазку"), KeyboardButton(text="🗺 Карта")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="📄 Документы")],
            [KeyboardButton(text="👥 Команда"), KeyboardButton(text="📊 Статус")],
            [KeyboardButton(text="📜 Помощь"), KeyboardButton(text="🔄 Сначала")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие…",
    )

def scene_keyboard(scene_id: str, player: PlayerState) -> InlineKeyboardMarkup:
    scene = SCENES[scene_id]
    rows = [[InlineKeyboardButton(text=text, callback_data=f"go:{next_id}")] for text, next_id in scene["choices"]]
    if player.maps:
        rows.append([InlineKeyboardButton(text="🗺 Открыть мини-карту", url=build_map_url(scene_id, player.maps))])
    rows.append([
        InlineKeyboardButton(text="🎒 Инвентарь", callback_data="menu:inventory"),
        InlineKeyboardButton(text="📄 Документы", callback_data="menu:documents"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def build_map_url(scene_id: str, maps: Set[str]) -> str:
    state = SCENE_TO_MAP_STATE.get(scene_id, "day1_yard")
    maps_param = ",".join([m for m in ["floor1", "tech", "underground"] if m in maps])
    return f"{MAP_URL}?state={state}&maps={maps_param}"

def map_keyboard(scene_id: str, maps: Set[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Открыть мини-карту", url=build_map_url(scene_id, maps))]
    ])

def format_scene(scene_id: str, notices: Optional[List[str]] = None) -> str:
    scene = SCENES.get(scene_id, SCENES["start"])
    title = scene.get("title", "Сцена")
    text = scene["text"]
    extra = ""
    if notices:
        extra = "\n\n" + "\n".join(notices)
    return f"▌ {title}\n\n{text}{extra}"

def map_status_text(player: PlayerState) -> str:
    if not player.maps:
        return "🗺 Карта недоступна.\n\nУ тебя нет карты комплекса. Сейчас ты ориентируешься только по памяти, указателям и словам команды. Найди служебную схему на локации."
    opened = "\n".join(f"✓ {MAP_LABELS[m]}" for m in ["floor1", "tech", "underground"] if m in player.maps)
    return f"🗺 Открытые карты:\n\n{opened}"

def inventory_text(player: PlayerState) -> str:
    if not player.items:
        return "🎒 Инвентарь пуст.\n\nПредметы появляются только после конкретных действий в сценах."
    items = "\n".join(f"• {ITEM_LABELS[item]}" for item in sorted(player.items))
    return f"🎒 Инвентарь:\n\n{items}"

def documents_text(player: PlayerState) -> str:
    if not player.docs:
        return "📄 Документы не найдены.\n\nИщи журналы, служебные записки и папки комплекса."
    docs = "\n".join(f"• {DOC_LABELS[doc]}" for doc in sorted(player.docs))
    return f"📄 Найденные документы:\n\n{docs}"

def status_text(player: PlayerState) -> str:
    scene_title = SCENES.get(player.scene, SCENES["start"]).get("title", player.scene)
    return (
        "📊 Статус прохождения\n\n"
        f"Текущая сцена: {scene_title}\n"
        f"Карт найдено: {len(player.maps)} / 3\n"
        f"Предметов найдено: {len(player.items)}\n"
        f"Документов найдено: {len(player.docs)}"
    )

async def send_scene(message_or_query, user_id: int, scene_id: str):
    player = get_player(user_id)
    player.scene = scene_id
    notices = apply_effects(player, scene_id)
    text = format_scene(scene_id, notices)
    markup = scene_keyboard(scene_id, player)

    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.answer(text, reply_markup=markup)
    else:
        await message_or_query.answer(text, reply_markup=markup)

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        get_player(message.from_user.id)
        await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())

    @dp.message(Command("play"))
    @dp.message(F.text == "▶️ Начать вылазку")
    async def play(message: types.Message):
        player = get_player(message.from_user.id)
        await send_scene(message, message.from_user.id, player.scene)

    @dp.message(Command("restart"))
    @dp.message(F.text == "🔄 Сначала")
    async def restart(message: types.Message):
        reset_player(message.from_user.id)
        await message.answer("Прогресс сброшен. Ворота «Периметра» снова закрыты.", reply_markup=main_menu_keyboard())
        await send_scene(message, message.from_user.id, "start")

    @dp.message(Command("map"))
    @dp.message(F.text == "🗺 Карта")
    async def map_cmd(message: types.Message):
        player = get_player(message.from_user.id)
        if player.maps:
            await message.answer(map_status_text(player), reply_markup=map_keyboard(player.scene, player.maps))
        else:
            await message.answer(map_status_text(player))

    @dp.message(Command("inventory"))
    @dp.message(F.text == "🎒 Инвентарь")
    async def inventory_cmd(message: types.Message):
        await message.answer(inventory_text(get_player(message.from_user.id)))

    @dp.message(Command("documents"))
    @dp.message(F.text == "📄 Документы")
    async def documents_cmd(message: types.Message):
        await message.answer(documents_text(get_player(message.from_user.id)))

    @dp.message(Command("team"))
    @dp.message(F.text == "👥 Команда")
    async def team_cmd(message: types.Message):
        await message.answer(TEAM_TEXT)

    @dp.message(Command("status"))
    @dp.message(F.text == "📊 Статус")
    async def status_cmd(message: types.Message):
        await message.answer(status_text(get_player(message.from_user.id)))

    @dp.message(Command("help"))
    @dp.message(F.text == "📜 Помощь")
    async def help_cmd(message: types.Message):
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())

    @dp.callback_query(lambda c: c.data.startswith("go:"))
    async def go(callback: CallbackQuery):
        scene_id = callback.data.split(":", 1)[1]
        await callback.answer()
        await send_scene(callback, callback.from_user.id, scene_id)

    @dp.callback_query(lambda c: c.data == "menu:inventory")
    async def callback_inventory(callback: CallbackQuery):
        await callback.answer()
        await callback.message.answer(inventory_text(get_player(callback.from_user.id)))

    @dp.callback_query(lambda c: c.data == "menu:documents")
    async def callback_documents(callback: CallbackQuery):
        await callback.answer()
        await callback.message.answer(documents_text(get_player(callback.from_user.id)))

    @dp.message()
    async def fallback(message: types.Message):
        await message.answer("Я не понял команду. Используй кнопки меню или /help.", reply_markup=main_menu_keyboard())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
