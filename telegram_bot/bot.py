from __future__ import annotations

import asyncio, html, json, os, sqlite3, tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from telegram_bot.image_factory import ensure_images
from telegram_bot.scenario import ACT_NAMES, get_documents, get_scenes

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
ensure_images(BASE_DIR)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "8196658213").replace(",", " ").split() if x.strip().isdigit()}
DB_PATH = Path(os.getenv("DB_PATH", "/data/perimetr.sqlite3" if Path("/data").exists() else str(BASE_DIR / "data" / "perimetr.sqlite3")))
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Добавьте его в переменные Amvera или в .env")

SCENES = get_scenes()
DOCUMENTS = get_documents()
ACT_START = {1: "SCENE_001", 2: "SCENE_201", 3: "SCENE_401"}

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def h(x: Any) -> str:
    return html.escape(str(x))


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,state_json TEXT NOT NULL,updated_at TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,scene_id TEXT,choice_id TEXT,event_json TEXT,created_at TEXT)")
        conn.commit()


def default_state() -> Dict[str, Any]:
    return {
        "current_scene": None,
        "unlocked_act": 1,
        "act1_completed": False,
        "act2_completed": False,
        "game_completed": False,
        "visited": [],
        "journal": [],
        "codex": [],
        "choice_log": [],
        "settings": {"images": True, "text_mode": "full"},
        "vars": {"trust_artem": 0, "trust_marina": 0, "trust_gleb": 0, "trust_eva": 0, "trust_team": 0, "knowledge": 0, "fear": 0, "contamination": 0, "morality_people": 0, "morality_truth": 0, "time_pressure": 0},
        "flags": {"first_phrase": "Сначала план, потом нервы.", "profile_complete": False, "profile_trait": "не определён", "profile_answers": [], "player_theory": "", "ng_plus_unlocked": False},
    }


def merge_state(state: Dict[str, Any]) -> Dict[str, Any]:
    base = default_state()
    for k, v in base.items():
        state.setdefault(k, v)
    for group in ["settings", "vars", "flags"]:
        state.setdefault(group, {})
        for k, v in base[group].items():
            state[group].setdefault(k, v)
    return state


def get_state(user_id: int) -> Dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT state_json FROM users WHERE user_id=?", (user_id,)).fetchone()
    if row:
        return merge_state(json.loads(row["state_json"]))
    state = default_state()
    save_state(user_id, state)
    return state


def save_state(user_id: int, state: Dict[str, Any]) -> None:
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO users(user_id,state_json,updated_at) VALUES(?,?,?)", (user_id, json.dumps(state, ensure_ascii=False), datetime.utcnow().isoformat()))
        conn.commit()


def log_event(user_id: int, scene_id: str, choice_id: str, choice_text: str) -> None:
    with db() as conn:
        conn.execute("INSERT INTO events(user_id,scene_id,choice_id,event_json,created_at) VALUES(?,?,?,?,?)", (user_id, scene_id, choice_id, json.dumps({"text": choice_text}, ensure_ascii=False), datetime.utcnow().isoformat()))
        conn.commit()


def clamp(state: Dict[str, Any]) -> None:
    for key in ["fear", "contamination", "time_pressure"]:
        state["vars"][key] = max(0, min(10, float(state["vars"].get(key, 0))))
    for key in ["trust_artem", "trust_marina", "trust_gleb", "trust_eva", "trust_team"]:
        state["vars"][key] = max(-5, min(5, float(state["vars"].get(key, 0))))


def apply_effects(state: Dict[str, Any], effects: Optional[Dict[str, Any]]) -> None:
    if not effects:
        return
    for key, value in effects.get("vars", {}).items():
        old = state["vars"].get(key, 0)
        state["vars"][key] = old + value if isinstance(old, (int, float)) and isinstance(value, (int, float)) else value
    for key, value in effects.get("flags", {}).items():
        state["flags"][key] = value
    for doc_id in effects.get("docs", []) or []:
        if doc_id in DOCUMENTS and doc_id not in state["codex"]:
            state["codex"].append(doc_id)
            state["journal"].append(f"Найден документ: {DOCUMENTS[doc_id]['title']}.")
    if effects.get("complete_act") == 1:
        state["act1_completed"], state["unlocked_act"] = True, max(state.get("unlocked_act", 1), 2)
    if effects.get("complete_act") == 2:
        state["act2_completed"], state["unlocked_act"] = True, max(state.get("unlocked_act", 1), 3)
    if effects.get("unlock_act"):
        state["unlocked_act"] = max(state.get("unlocked_act", 1), int(effects["unlock_act"]))
    if effects.get("complete_game"):
        state["game_completed"] = True
        state["flags"]["ng_plus_unlocked"] = True
    clamp(state)


def progress_text(state: Dict[str, Any]) -> str:
    return f"Пройдено сцен: {len(state['visited'])}/530\nОткрытый акт: {state.get('unlocked_act', 1)}/3\nТекущая сцена: {state.get('current_scene') or 'нет'}\nДокументы: {len(state['codex'])}\nПсихопрофиль: {state['flags'].get('profile_trait', 'не определён')}"


def split_text(text: str, limit: int = 3600) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts, buf = [], ""
    for p in text.split("\n\n"):
        if len(buf) + len(p) + 2 < limit:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                parts.append(buf)
            buf = p
    if buf:
        parts.append(buf)
    return parts


def menu_kb(state: Dict[str, Any]) -> InlineKeyboardMarkup:
    first = "Продолжить вылазку" if state.get("current_scene") else "Начать вылазку"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=first, callback_data="menu:start")],
        [InlineKeyboardButton(text="Акты", callback_data="menu:acts"), InlineKeyboardButton(text="Досье", callback_data="menu:dossier")],
        [InlineKeyboardButton(text="Журнал", callback_data="quick:journal"), InlineKeyboardButton(text="Карта", callback_data="quick:map")],
        [InlineKeyboardButton(text="Психопрофиль", callback_data="menu:profile"), InlineKeyboardButton(text="Настройки", callback_data="quick:settings")],
    ])


def act_kb(state: Dict[str, Any]) -> InlineKeyboardMarkup:
    rows = []
    for act in [1, 2, 3]:
        locked = act > int(state.get("unlocked_act", 1))
        done = state.get(f"act{act}_completed", False) if act < 3 else state.get("game_completed", False)
        label = f"🔒 Акт {act} · {ACT_NAMES[act]}" if locked else f"✓ Акт {act} · {ACT_NAMES[act]}" if done else f"▶ Акт {act} · {ACT_NAMES[act]}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"act:{act}")])
    rows.append([InlineKeyboardButton(text="Главное меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def choice_kb(scene_id: str, choices: list[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=c["text"], callback_data=f"choice:{scene_id}:{c['id']}")] for c in choices]
    rows.append([InlineKeyboardButton(text="Журнал", callback_data="quick:journal"), InlineKeyboardButton(text="Карта", callback_data="quick:map")])
    rows.append([InlineKeyboardButton(text="Меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_kb(step: int) -> InlineKeyboardMarkup:
    data = {1: [("Сначала порядок", "order"), ("Сначала люди", "people"), ("Сначала сигнал", "truth")], 2: [("Проверить рацию", "radio"), ("Разбудить команду", "team"), ("Промолчать и слушать", "silence")], 3: [("Спасти раненого", "save"), ("Забрать доказательства", "evidence"), ("Разделить команду", "split")]}
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"profile:{step}:{v}")] for t, v in data[step]])


def render_map(state: Dict[str, Any]) -> str:
    visited = set(state.get("visited", []))
    unlocked = state.get("unlocked_act", 1)
    return "<b>Карта объекта</b>\n\n" + "\n".join([
        "КПП — " + ("позади" if "SCENE_016" in visited else "перед входом"),
        "Административный корпус — доступен",
        "Столовая — " + ("лагерь" if "SCENE_106" in visited else "не найдена"),
        "Подземный уровень — " + ("открыт" if unlocked >= 2 else "закрыт"),
        "Центральный контур — " + ("открыт" if unlocked >= 3 else "закрыт"),
    ])


async def send_menu(chat_id: int, user_id: int, intro: Optional[str] = None) -> None:
    state = get_state(user_id)
    caption = intro or ("<b>НИИ «Периметр»</b>\nКанал связи восстановлен.\n\n<i>Акт II и Акт III закрыты до прохождения предыдущих.</i>\n\n" + h(progress_text(state)))
    img = BASE_DIR / "assets" / "images" / "start_screen.png"
    if state["settings"].get("images", True) and img.exists():
        await bot.send_photo(chat_id, FSInputFile(img), caption=caption, reply_markup=menu_kb(state))
    else:
        await bot.send_message(chat_id, caption, reply_markup=menu_kb(state))


async def send_scene(chat_id: int, user_id: int, scene_id: str) -> None:
    state = get_state(user_id)
    scene = SCENES.get(scene_id)
    if not scene:
        await bot.send_message(chat_id, f"Сцена не найдена: {h(scene_id)}")
        return
    state["current_scene"] = scene_id
    if scene_id not in state["visited"]:
        state["visited"].append(scene_id)
    apply_effects(state, scene.get("effects_on_enter"))
    save_state(user_id, state)
    header = f"◆ <b>Акт {scene['act']} · {h(scene['act_name'])}</b>\n<i>{h(scene['time'])} · {h(scene['location'])}</i>\n━━━━━━━━━━━━\n<b>{h(scene['title'])}</b>"
    text = scene["text"].replace("{player_echo}", f"«{state['flags'].get('first_phrase')}»")
    if state["settings"].get("text_mode") == "short" and len(text) > 800:
        text = text.split("\n\n")[0]
    body = header + "\n\n" + h(text)
    img_ref = scene.get("image")
    if img_ref and state["settings"].get("images", True):
        img = BASE_DIR / img_ref
        if img.exists():
            try:
                await bot.send_photo(chat_id, FSInputFile(img), caption=header)
                body = h(text)
            except Exception:
                pass
    for i, part in enumerate(split_text(body)):
        await bot.send_message(chat_id, part, reply_markup=choice_kb(scene_id, scene["choices"]) if i == len(split_text(body)) - 1 else None)


async def finish_act(chat_id: int, user_id: int, act: int) -> None:
    state = get_state(user_id)
    state["current_scene"] = None
    state[f"act{act}_completed"] = True
    state["unlocked_act"] = max(state.get("unlocked_act", 1), act + 1)
    state["journal"].append(f"Акт {act} завершён: {ACT_NAMES[act]}.")
    save_state(user_id, state)
    await bot.send_message(chat_id, f"Акт {act} завершён. Следующий акт открыт.", reply_markup=act_kb(state))


async def finish_game(chat_id: int, user_id: int) -> None:
    state = get_state(user_id)
    state["current_scene"] = None
    state["game_completed"] = True
    state["flags"]["ng_plus_unlocked"] = True
    save_state(user_id, state)
    await bot.send_message(chat_id, "Игра завершена. NG+ открыт. /new начнёт новую вылазку.")


@dp.message(Command("start", "menu"))
async def cmd_start(message: Message) -> None:
    await send_menu(message.chat.id, message.from_user.id, "<b>НИИ «Периметр»</b>\nНа экране мигает: <i>ВЫЛАЗКА №1 ГОТОВА</i>.\n\n" + h(progress_text(get_state(message.from_user.id))))


@dp.message(Command("acts"))
async def cmd_acts(message: Message) -> None:
    await message.answer("Выберите акт.", reply_markup=act_kb(get_state(message.from_user.id)))


@dp.message(Command("continue", "play"))
async def cmd_continue(message: Message) -> None:
    state = get_state(message.from_user.id)
    await send_scene(message.chat.id, message.from_user.id, state["current_scene"]) if state.get("current_scene") else await cmd_acts(message)


@dp.message(Command("new", "restart"))
async def cmd_new(message: Message) -> None:
    save_state(message.from_user.id, default_state())
    await send_menu(message.chat.id, message.from_user.id, "Новая вылазка начата.")


@dp.message(Command("journal"))
async def cmd_journal(message: Message) -> None:
    entries = get_state(message.from_user.id).get("journal", [])[-20:]
    await message.answer("<b>Журнал</b>\n\n" + ("\n".join("• " + h(e) for e in entries) if entries else "Пока пусто."))


@dp.message(Command("codex"))
async def cmd_codex(message: Message) -> None:
    ids = get_state(message.from_user.id).get("codex", [])
    if not ids:
        await message.answer("Кодекс пуст.")
        return
    lines = ["<b>Кодекс</b>"]
    for did in ids:
        d = DOCUMENTS.get(did)
        if d:
            lines.append(f"\n<b>{h(d['title'])}</b>\n<i>{h(d['category'])}</i>\n{h(d['summary'])}")
    await message.answer("\n".join(lines))


@dp.message(Command("map"))
async def cmd_map(message: Message) -> None:
    await message.answer(render_map(get_state(message.from_user.id)))


@dp.message(Command("status"))
async def cmd_status(message: Message) -> None:
    s = get_state(message.from_user.id)
    v = s["vars"]
    mood = lambda x: "держится рядом" if x >= 1 else "отдаляется" if x <= -1 else "насторожен"
    await message.answer(f"<b>Состояние</b>\nСцена: {h(s.get('current_scene') or 'нет')}\nАкт: {s.get('unlocked_act')}\n\nАртём: {mood(v.get('trust_artem', 0))}\nМарина: {mood(v.get('trust_marina', 0))}\nГлеб: {mood(v.get('trust_gleb', 0))}\nЕва: {mood(v.get('trust_eva', 0))}")


@dp.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    s = get_state(message.from_user.id)["settings"]
    await message.answer("<b>Настройки</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Картинки: {'вкл' if s.get('images') else 'выкл'}", callback_data="settings:images")],
        [InlineKeyboardButton(text=f"Текст: {'короткий' if s.get('text_mode') == 'short' else 'полный'}", callback_data="settings:text")],
    ]))


@dp.message(Command("note", "theory"))
async def cmd_note(message: Message, command: CommandObject) -> None:
    text = (command.args or "").strip()
    if not text:
        await message.answer("Напишите текст после команды.")
        return
    state = get_state(message.from_user.id)
    prefix = "Гипотеза игрока: " if message.text.startswith("/theory") else "Личная заметка: "
    state["journal"].append(prefix + text[:600])
    if message.text.startswith("/theory"):
        state["flags"]["player_theory"] = text[:700]
    save_state(message.from_user.id, state)
    await message.answer("Сохранено.")


@dp.message(Command("admin", "debug_status", "goto", "set", "export_save"))
async def admin_commands(message: Message, command: CommandObject) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет доступа.")
        return
    cmd = message.text.split()[0].lstrip("/").split("@")[0]
    args = command.args or ""
    if cmd == "admin":
        await message.answer("/goto SCENE_001\n/debug_status\n/set fear 5\n/export_save user_id")
    elif cmd == "debug_status":
        await message.answer("<pre>" + h(json.dumps(get_state(message.from_user.id), ensure_ascii=False, indent=2)) + "</pre>")
    elif cmd == "goto":
        await send_scene(message.chat.id, message.from_user.id, args.strip().upper())
    elif cmd == "set":
        parts = args.split(maxsplit=1)
        if len(parts) == 2:
            state = get_state(message.from_user.id)
            try: value: Any = float(parts[1])
            except ValueError: value = parts[1]
            state["vars"][parts[0]] = value
            clamp(state); save_state(message.from_user.id, state)
            await message.answer("Установлено.")
    elif cmd == "export_save":
        target = int(args.strip() or message.from_user.id)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:
            json.dump(get_state(target), f, ensure_ascii=False, indent=2)
            path = f.name
        await message.answer_document(FSInputFile(path), caption=f"Сохранение {target}")


@dp.callback_query(F.data.startswith("menu:"))
async def cb_menu(c: CallbackQuery) -> None:
    action = c.data.split(":", 1)[1]
    state = get_state(c.from_user.id)
    await c.answer()
    if action == "home": await send_menu(c.message.chat.id, c.from_user.id)
    elif action == "acts": await c.message.answer("Выберите акт.", reply_markup=act_kb(state))
    elif action == "dossier": await c.message.answer("<b>Досье</b>\nГлеб — безопасность. Марина — инженер. Артём — связь. Ева — врач. Вы — точка решения.", reply_markup=menu_kb(state))
    elif action == "profile": await send_profile(c.message.chat.id, c.from_user.id, 1)
    elif action == "start":
        if not state["flags"].get("profile_complete"):
            await send_profile(c.message.chat.id, c.from_user.id, 1)
        elif state.get("current_scene"):
            await send_scene(c.message.chat.id, c.from_user.id, state["current_scene"])
        else:
            await c.message.answer("Выберите акт.", reply_markup=act_kb(state))


async def send_profile(chat_id: int, user_id: int, step: int) -> None:
    q = {1: "Психопрофиль 1/3. Что важнее в первые минуты?", 2: "Психопрофиль 2/3. Рация шепчет вашим голосом. Что вы делаете?", 3: "Психопрофиль 3/3. Раненый человек и архив. Ваш импульс?"}[step]
    await bot.send_message(chat_id, q, reply_markup=profile_kb(step))


@dp.callback_query(F.data.startswith("profile:"))
async def cb_profile(c: CallbackQuery) -> None:
    _, step_raw, value = c.data.split(":")
    step = int(step_raw)
    state = get_state(c.from_user.id)
    state["flags"].setdefault("profile_answers", []).append({"step": step, "value": value})
    if step == 1:
        state["flags"]["first_phrase"] = {"order": "Сначала порядок. Потом страх.", "people": "Живые важнее протокола.", "truth": "Сигнал важнее тишины."}[value]
    if step == 3:
        state["flags"]["profile_complete"] = True
        state["flags"]["profile_trait"] = {"save": "защитник", "evidence": "следователь", "split": "координатор"}[value]
        state["journal"].append("Психопрофиль завершён.")
    save_state(c.from_user.id, state)
    await c.answer()
    if step < 3:
        await send_profile(c.message.chat.id, c.from_user.id, step + 1)
    else:
        await c.message.answer("Психопрофиль завершён.", reply_markup=act_kb(state))


@dp.callback_query(F.data.startswith("act:"))
async def cb_act(c: CallbackQuery) -> None:
    act = int(c.data.split(":")[1])
    state = get_state(c.from_user.id)
    if act > int(state.get("unlocked_act", 1)):
        await c.answer("Этот акт ещё закрыт", show_alert=True)
        return
    await c.answer()
    await send_scene(c.message.chat.id, c.from_user.id, ACT_START[act])


@dp.callback_query(F.data.startswith("quick:"))
async def cb_quick(c: CallbackQuery) -> None:
    action = c.data.split(":", 1)[1]
    await c.answer()
    if action == "journal": await c.message.answer("\n".join("• " + h(e) for e in get_state(c.from_user.id).get("journal", [])[-20:]) or "Журнал пуст.")
    elif action == "map": await c.message.answer(render_map(get_state(c.from_user.id)))
    elif action == "settings": await cmd_settings(c.message)


@dp.callback_query(F.data.startswith("settings:"))
async def cb_settings(c: CallbackQuery) -> None:
    key = c.data.split(":", 1)[1]
    state = get_state(c.from_user.id)
    if key == "images": state["settings"]["images"] = not state["settings"].get("images", True)
    if key == "text": state["settings"]["text_mode"] = "short" if state["settings"].get("text_mode") == "full" else "full"
    save_state(c.from_user.id, state)
    await c.answer("Сохранено")
    await cmd_settings(c.message)


@dp.callback_query(F.data.startswith("choice:"))
async def cb_choice(c: CallbackQuery) -> None:
    _, sid, cid = c.data.split(":", 2)
    state = get_state(c.from_user.id)
    if state.get("current_scene") != sid:
        await c.answer("Этот выбор уже неактуален", show_alert=True)
        return
    scene = SCENES.get(sid)
    choice = next((x for x in scene["choices"] if x["id"] == cid), None) if scene else None
    if not choice:
        await c.answer("Выбор не найден", show_alert=True)
        return
    apply_effects(state, choice.get("effects"))
    state["choice_log"].append({"scene": sid, "choice": cid, "at": datetime.utcnow().isoformat()})
    log_event(c.from_user.id, sid, cid, choice["text"])
    save_state(c.from_user.id, state)
    await c.answer()
    effects = choice.get("effects", {})
    if effects.get("complete_game"): await finish_game(c.message.chat.id, c.from_user.id); return
    if effects.get("complete_act"): await finish_act(c.message.chat.id, c.from_user.id, int(effects["complete_act"])); return
    await send_scene(c.message.chat.id, c.from_user.id, choice["next"])


async def main() -> None:
    init_db()
    print(f"Perimeter bot started. Scenes: {len(SCENES)}. DB: {DB_PATH}", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
