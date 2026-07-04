import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAP_URL = os.getenv("MAP_URL", "https://wwgame28.github.io/perimeter/web_map/")

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
        "choices": [("🟦 Проверить генератор", "hall"), ("🟥 Открыть гараж", "hall"), ("🟩 Позвать остальных", "hall")],
    },
    "hall": {
        "text": "Холл пуст. Часы на стене остановились на 03:07. На стойке регистрации лежит журнал посещений. В нём есть фамилии людей, которых фонд не упоминал.",
        "choices": [("Начать заново", "start")],
    },
}

SCENE_TO_MAP_STATE = {
    "start": "day1_start",
    "fedor": "day1_start",
    "gate": "day1_start",
    "team": "day1_start",
    "yard": "day1_yard",
    "hall": "day1_yard",
}

user_scene = {}

def keyboard(scene_id: str):
    scene = SCENES[scene_id]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"go:{next_id}")]
        for text, next_id in scene["choices"]
    ])

def map_keyboard(scene_id: str):
    state = SCENE_TO_MAP_STATE.get(scene_id, "day1_yard")
    url = f"{MAP_URL}?state={state}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Открыть карту", url=url)]
    ])

async def send_scene(message_or_query, scene_id: str):
    scene = SCENES.get(scene_id, SCENES["start"])
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.answer(scene["text"], reply_markup=keyboard(scene_id))
    else:
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
        await send_scene(message, "start")

    @dp.message(Command("map"))
    async def map_cmd(message: types.Message):
        scene_id = user_scene.get(message.from_user.id, "start")
        await message.answer("Карта текущего положения команды:", reply_markup=map_keyboard(scene_id))

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
