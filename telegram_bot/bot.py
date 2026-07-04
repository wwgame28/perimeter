import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAP_URL = os.getenv("MAP_URL", "https://wwgame28.github.io/perimeter/web_map/")

MAP_LABELS = {
    "floor1": "Этаж 1",
    "tech": "Технический уровень",
    "underground": "Подземный уровень",
}

SCENES = {
    "start": {
        "text": "Ты стоишь у ворот исследовательского центра «Периметр». За спиной — мокрый лес. Впереди — объект, где пропала первая группа.\n\nФёдор, сторож КПП, смотрит на тебя и говорит: «Если услышишь знакомый голос — не отвечай». Как поступишь?",
        "choices": [
            ("🟦 Расспросить Фёдора", "fedor"),
            ("🟥 Потребовать открыть ворота", "gate"),
            ("🟩 Поблагодарить и предупредить команду", "team"),
        ],
    },
    "fedor": {
        "text": "Фёдор долго молчит. Потом говорит: «Ночью здесь зовут голосами умерших. Я не знаю, что это. Но отвечать нельзя». Ты запоминаешь предупреждение.",
        "choices": [("Продолжить", "gate")],
    },
    "gate": {
        "text": "Ворота медленно открываются. Металл скрипит так, будто комплекс просыпается. Команда входит внутрь. Назад дороги уже нет.",
        "choices": [("🟦 Осмотреть двор", "yard"), ("🟥 Идти прямо в холл", "hall"), ("🟩 Проверить команду", "team")],
    },
    "team": {
        "text": "Глеб проверяет карту. Марина смотрит на здание. Артём нервно шутит. Ева держит аптечку так крепко, будто уже знает, что она понадобится.",
        "choices": [("Продолжить ко входу", "gate")],
    },
    "yard": {
        "text": "Во дворе ржавые бочки, старый генератор и следы шин. Где-то внутри комплекса коротко включается динамик: «Внимание... аварийный...» — и замолкает.",
        "choices": [("🟦 Проверить генератор", "generator"), ("🟥 Открыть гараж", "garage"), ("🟩 Позвать остальных", "hall")],
    },
    "garage": {
        "text": "В гараже пахнет бензином и мокрым металлом. На верстаке лежит старый фонарь, несколько инструментов и лист с половиной схемы объекта. Это не карта, но она подтверждает: у здания есть технический уровень.",
        "choices": [("🟦 Забрать инструменты", "hall"), ("🟥 Открыть склад", "generator"), ("🟩 Вернуться к команде", "hall")],
    },
    "hall": {
        "text": "Холл пуст. Часы на стене остановились на 03:07. На стойке регистрации лежит журнал посещений. Под ним — сложенная бумажная схема: «ЭТАЖ 1. СЛУЖЕБНЫЙ ПЛАН».\n\n🗺 Найдена карта первого этажа. Теперь команда может ориентироваться в верхнем уровне комплекса.",
        "effects": {"unlock_map": "floor1"},
        "choices": [("🟦 Открыть карту", "map_hint"), ("🟥 Идти в архив", "archive"), ("🟩 Собрать команду", "canteen")],
    },
    "map_hint": {
        "text": "Ты разворачиваешь бумагу. Чернила расплылись от влаги, но основные зоны читаются: КПП, внутренний двор, гараж, медпункт, холл, архив, серверная и лаборатории.\n\nТеперь командой можно пользоваться командой /map.",
        "choices": [("Продолжить", "archive")],
    },
    "archive": {
        "text": "В архиве пахнет пылью и растворителем. В одном из шкафов лежит папка «Служебные коммуникации». Между страницами — схема кабельных тоннелей и генераторной.\n\n🗺 Найдена карта технического уровня.",
        "effects": {"unlock_map": "tech"},
        "choices": [("🟦 Изучить схему", "generator"), ("🟥 Спуститься вниз", "underground_map"), ("🟩 Вернуться в столовую", "canteen")],
    },
    "generator": {
        "text": "Генераторная дрожит от низкого гула. На стене висит служебный щит с пометками вентиляции, электрощитовой и химического склада. Теперь понятно, как технический уровень связан с распространением PX-17.",
        "effects": {"unlock_map": "tech"},
        "choices": [("🟦 Отключить часть питания", "underground_map"), ("🟥 Идти дальше по тоннелю", "underground_map"), ("🟩 Вернуться к остальным", "canteen")],
    },
    "underground_map": {
        "text": "За технической дверью обнаружена старая папка с красной печатью: «ПОДЗЕМНЫЙ УРОВЕНЬ. ДОСТУП 4». Бумага влажная, но на ней видны: испытательные камеры, хранилище PX-17 и центральная лаборатория.\n\n🗺 Найдена карта подземного уровня.",
        "effects": {"unlock_map": "underground"},
        "choices": [("🟦 Открыть карту", "final_lab"), ("🟥 Идти в хранилище PX-17", "final_lab"), ("🟩 Позвать команду", "canteen")],
    },
    "canteen": {
        "text": "Столовая становится временным лагерем. На столе лежат найденные карты, документы и фонари. Теперь объект больше не кажется непонятным лабиринтом — но от этого он не стал безопаснее.",
        "choices": [("Продолжить", "final_lab")],
    },
    "final_lab": {
        "text": "Все найденные карты сходятся в одной точке: центральная лаборатория PX-17. Именно туда ведут маршруты, следы и чужие записи. Дальше будет не вопрос пути. Дальше будет вопрос выбора.",
        "choices": [("Начать заново", "start")],
    },
}

SCENE_TO_MAP_STATE = {
    "start": "day1_start",
    "fedor": "day1_start",
    "gate": "day1_start",
    "team": "day1_start",
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

user_scene = {}
user_maps = {}

def apply_effects(user_id: int, scene_id: str):
    scene = SCENES.get(scene_id, {})
    effects = scene.get("effects", {})
    if "unlock_map" in effects:
        user_maps.setdefault(user_id, set()).add(effects["unlock_map"])


def keyboard(scene_id: str):
    scene = SCENES[scene_id]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"go:{next_id}")]
        for text, next_id in scene["choices"]
    ])


def map_keyboard(scene_id: str, maps: set[str]):
    state = SCENE_TO_MAP_STATE.get(scene_id, "day1_yard")
    maps_param = ",".join([m for m in ["floor1", "tech", "underground"] if m in maps])
    url = f"{MAP_URL}?state={state}&maps={maps_param}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Открыть мини-карту", url=url)]
    ])


def map_status_text(maps: set[str]) -> str:
    if not maps:
        return "У тебя нет карты комплекса. Сейчас ты ориентируешься только по памяти, указателям и словам команды."
    opened = ", ".join(MAP_LABELS[m] for m in ["floor1", "tech", "underground"] if m in maps)
    return f"Открытые карты: {opened}."


async def send_scene(message_or_query, scene_id: str):
    scene = SCENES.get(scene_id, SCENES["start"])
    if isinstance(message_or_query, CallbackQuery):
        user_id = message_or_query.from_user.id
        apply_effects(user_id, scene_id)
        await message_or_query.message.answer(scene["text"], reply_markup=keyboard(scene_id))
    else:
        user_id = message_or_query.from_user.id
        apply_effects(user_id, scene_id)
        await message_or_query.answer(scene["text"], reply_markup=keyboard(scene_id))


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer("Добро пожаловать в «Периметр». Команды: /play, /map, /team")

    @dp.message(Command("play"))
    async def play(message: types.Message):
        user_scene[message.from_user.id] = "start"
        user_maps[message.from_user.id] = set()
        await send_scene(message, "start")

    @dp.message(Command("map"))
    async def map_cmd(message: types.Message):
        user_id = message.from_user.id
        scene_id = user_scene.get(user_id, "start")
        maps = user_maps.get(user_id, set())
        await message.answer(map_status_text(maps), reply_markup=map_keyboard(scene_id, maps))

    @dp.message(Command("team"))
    async def team(message: types.Message):
        await message.answer("Команда: игрок, Глеб, Марина, Артём, Ева и другие участники экспедиции. Главный герой — силуэт, чтобы им мог быть любой игрок.")

    @dp.callback_query(lambda c: c.data.startswith("go:"))
    async def go(callback: CallbackQuery):
        scene_id = callback.data.split(":", 1)[1]
        user_scene[callback.from_user.id] = scene_id
        await callback.answer()
        await send_scene(callback, scene_id)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
