import asyncio, json, os, random, sqlite3, threading, html
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BASE = Path(__file__).resolve().parent
TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMINS = {int(x) for x in os.getenv('ADMIN_IDS', '8196658213').split(',') if x.strip().isdigit()}
DB = Path(os.getenv('DB_PATH', str(BASE / 'data' / 'perimetr.sqlite3')))
PORT = int(os.getenv('PORT', '8080'))
SCENES: Dict[str, Dict[str, Any]] = {}

IMAGES = {
    'SCENE_001': 'start_screen.png', 'SCENE_016': 'fedor.png', 'SCENE_030': 'gates.png',
    'SCENE_045': 'artem.png', 'SCENE_048': 'marina.png', 'SCENE_052': 'gleb.png',
    'SCENE_056': 'eva.png', 'SCENE_090': 'generator.png', 'SCENE_120': 'sergey.png',
    'SCENE_201': 'empty_seat.png', 'SCENE_246': 'trial.png', 'SCENE_320': 'radio.png',
    'SCENE_361': 'second_night.png', 'SCENE_461': 'archive.png', 'SCENE_501': 'zorin.png',
    'SCENE_541': 'three_truths.png', 'SCENE_575': 'final_choice.png', 'SCENE_621': 'ng_plus.png'
}
SPECIAL = {
    'SCENE_001': ('Последняя спокойная дорога', 'Автобус подпрыгивает на бетонных плитах. За окнами мокрый лес. Артём шутит, Марина молчит, Ева листает папку, а Глеб слишком спокойно смотрит на карту.'),
    'SCENE_016': ('Фёдор у шлагбаума', 'Сторож открывает проход и говорит почти без голоса: «Если услышите свой голос — не отвечайте». После этой фразы даже дождь кажется тише.'),
    'SCENE_045': ('Фотография Сергея', 'Артём показывает фото брата. На снимке Сергей стоит у двери, которую никто ещё не видел внутри объекта.'),
    'SCENE_048': ('Разметка Марины', 'Марина находит инженерную метку с фамилией подрядчика. Она произносит имя слишком тихо, но вы понимаете: это связано с её отцом.'),
    'SCENE_052': ('Старое имя коридора', 'Глеб называет закрытый сектор старым служебным названием. На карте такого названия нет.'),
    'SCENE_056': ('Анкета Евы', 'Ева прячет медицинскую анкету с пометкой PX-17. Потом просит: «Если я начну оправдывать фонд — останови меня».'),
    'SCENE_090': ('Генератор и первое решение', 'На щите четыре линии: свет, связь, медблок, архив. Энергии хватит только на одно направление.'),
    'SCENE_120': ('Серёга?', 'Рация включается сама. Артём слышит голос брата и впервые перестаёт шутить.'),
    'SCENE_201': ('Пустое место за столом', 'Утром за столом одно место пустое. Кружка остыла, а на краю лежит предмет, которого ночью не было.'),
    'SCENE_246': ('Суд за столом', 'Команда пытается восстановить ночь. В каждой версии есть человек, который врёт — или помнит не то.'),
    'SCENE_320': ('Рация говорит вашим голосом', 'Из помех звучит ваш собственный голос. Он повторяет фразу из первого дня, но меняет одно слово.'),
    'SCENE_361': ('Не отвечайте, если услышите меня', 'Марина сидит рядом и молчит. Но её голос зовёт из коридора.'),
    'SCENE_461': ('Центральный архив', 'Здесь нет монстра. Только документы, которых слишком много, чтобы оправдаться незнанием.'),
    'SCENE_501': ('Зорин за стеклом', 'Зорин выглядит не злодеем, а человеком, который слишком долго объяснял себе компромиссы.'),
    'SCENE_541': ('Три правды', 'Перед вами имена погибших, формула PX-17 и путь наружу. Все три нельзя унести вместе.'),
    'SCENE_575': ('Выбор принят', 'Комплекс гудит так низко, что вибрация проходит через кости. Вы уже знаете достаточно.'),
    'SCENE_621': ('Фёдор закрывает журнал', 'В журнале у ворот уже есть ваша фамилия. Чернила свежие.'),
}


def sid(n): return f'SCENE_{n:03d}'
def act(s):
    n=int(s.split('_')[1]); return 1 if n<=120 else 2 if n<=380 else 3
def nxt(n, step=1):
    if n<=120: return sid(min(120,n+step))
    if n<=380: return sid(min(380,n+step))
    return sid(min(630,n+step))
def ch(label, next_id, effects=None): return {'label':label,'next':next_id,'effects':effects or {}}


def build_scenes():
    scenes={}; ids=list(range(1,121))+list(range(201,381))+list(range(401,631))
    short=['Тихий коридор','Пауза в рации','След на пыли','Дверь без номера','Сломанная камера','Лестница вниз']
    docs=['Обрывок отчёта','Журнал Фёдора','Протокол PX-17','Приказ фонда','Список недобровольцев']
    for i,n in enumerate(ids):
        s=sid(n); a=act(s)
        title,text=SPECIAL.get(s,(docs[i%len(docs)] if i%5==0 else short[i%len(short)],''))
        if not text:
            if i%5==0: text=f'Вы находите документ: «{title}». Он не объясняет всё, но меняет порядок вопросов.'
            else: text=f'{title}. Деталь цепляет взгляд: открытая защёлка, чужой след, пауза в шуме вентиляции. Комплекс будто ждёт, какой смысл вы сами этому дадите.'
        choices=[ch('Проверить деталь',nxt(n,1),{'knowledge':1}), ch('Пойти на звук',nxt(n,2),{'fear':1,'px17':1}), ch('Поговорить с тем, кто рядом',nxt(n,1),{'trust_team':1}), ch('Промолчать и наблюдать',nxt(n,1),{'inner_voice':1})]
        if i%5==0: choices=[ch('Забрать документ',nxt(n,1),{'knowledge':1,'doc':s}),ch('Сфотографировать страницу',nxt(n,2),{'evidence':1,'doc':s}),ch('Показать находку команде',nxt(n,1),{'trust_team':1,'doc':s})]
        if s=='SCENE_090': choices=[ch('Подать питание на свет',nxt(n,1),{'power_light':1}),ch('Подать питание на связь',nxt(n,2),{'power_radio':1}),ch('Подать питание на медблок',nxt(n,3),{'power_med':1}),ch('Подать питание на архив',nxt(n,4),{'power_archive':1,'knowledge':2})]
        if s=='SCENE_541': choices=[ch('Вынести имена погибших',nxt(n,4),{'people':1}),ch('Сохранить доказательства',nxt(n,2),{'truth':1,'evidence':2}),ch('Уничтожить формулу',nxt(n,3),{'formula_destroyed':1})]
        if s=='SCENE_120': choices=[ch('Остаться с Артёмом',None,{'act1':1,'unlock':2})]
        if s=='SCENE_380': choices=[ch('Войти в третий день',None,{'act2':1,'unlock':3})]
        if s=='SCENE_630': choices=[ch('Вернуться в меню',None,{'finished':1})]
        scenes[s]={'id':s,'act':a,'title':title,'text':text,'image':IMAGES.get(s),'choices':choices}
    return scenes


def dirs():
    (BASE/'assets'/'images').mkdir(parents=True,exist_ok=True); DB.parent.mkdir(parents=True,exist_ok=True)

def make_images():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception: return
    labels={v:k.replace('SCENE_','СЦЕНА ') for k,v in IMAGES.items()}; labels['start_screen.png']='НИИ ПЕРИМЕТР'
    for fn,title in labels.items():
        p=BASE/'assets'/'images'/fn
        if p.exists(): continue
        im=Image.new('RGB',(1280,720),(16,24,30)); d=ImageDraw.Draw(im); font=ImageFont.load_default()
        for y in range(720): d.line([(0,y),(1280,y)],fill=(16+y//18,24+y//22,30+y//26))
        d.rectangle([80,90,1200,630],outline=(150,160,155),width=2)
        d.rectangle([0,610,1280,720],fill=(8,10,12)); d.ellipse([1030,80,1120,170],fill=(145,140,112))
        d.text((96,520),title,font=font,fill=(235,232,215)); d.text((96,560),'если услышите свой голос — не отвечайте',font=font,fill=(170,176,170))
        im.save(p,'PNG',optimize=True)

def db():
    with sqlite3.connect(DB) as con: con.execute('create table if not exists saves(user_id integer primary key,state text,updated text)')
def default(): return {'scene':None,'unlock':1,'vars':{},'docs':[],'history':[],'notes':[],'images':True}
def load(uid):
    with sqlite3.connect(DB) as con: row=con.execute('select state from saves where user_id=?',(uid,)).fetchone()
    return json.loads(row[0]) if row else default()
def save(uid,state):
    with sqlite3.connect(DB) as con: con.execute('insert or replace into saves values(?,?,?)',(uid,json.dumps(state,ensure_ascii=False),datetime.utcnow().isoformat()))
def effects(state,e):
    for k,v in e.items():
        if k=='doc':
            if v not in state['docs']: state['docs'].append(v)
        elif k=='unlock': state['unlock']=max(state.get('unlock',1),int(v))
        else: state['vars'][k]=state['vars'].get(k,0)+v if isinstance(v,int) else v

def menu_kb(state):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Продолжить' if state.get('scene') else 'Начать вылазку',callback_data='m:cont')],[InlineKeyboardButton(text='Акты',callback_data='m:acts'),InlineKeyboardButton(text='Брифинг',callback_data='m:brief')],[InlineKeyboardButton(text='Журнал',callback_data='m:journal'),InlineKeyboardButton(text='Кодекс',callback_data='m:codex')],[InlineKeyboardButton(text='Карта',callback_data='m:map'),InlineKeyboardButton(text='Настройки',callback_data='m:set')]])
def scene_kb(scene):
    rows=[[InlineKeyboardButton(text=c['label'],callback_data=f"c:{scene['id']}:{i}")] for i,c in enumerate(scene['choices'])]
    rows += [[InlineKeyboardButton(text='Записать вывод',callback_data='m:note')],[InlineKeyboardButton(text='Меню',callback_data='m:home')]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
def acts_kb(state):
    u=state.get('unlock',1)
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Акт I: Вход',callback_data='a:1')],[InlineKeyboardButton(text='Акт II: Распад' if u>=2 else 'Акт II: закрыт',callback_data='a:2')],[InlineKeyboardButton(text='Акт III: Цена выбора' if u>=3 else 'Акт III: закрыт',callback_data='a:3')],[InlineKeyboardButton(text='Назад',callback_data='m:home')]])
def profile_kb(step):
    q=[[('Сначала люди','people'),('Сначала факты','truth'),('Сначала выход','exit')],[('Доверять команде','team'),('Проверять каждого','control'),('Слушать объект','echo')],[('Ответить голосу','answer'),('Промолчать','silent'),('Найти источник','source')]][step]
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t,callback_data=f'p:{step}:{v}')] for t,v in q])

async def send_menu(bot,chat,uid):
    st=load(uid); cap='<b>НИИ «Периметр»</b>\nДоступ восстановлен. Выборы не показывают цену — последствия проявятся позже.'
    img=BASE/'assets'/'images'/'start_screen.png'
    if st.get('images') and img.exists(): await bot.send_photo(chat,FSInputFile(img),caption=cap,reply_markup=menu_kb(st),parse_mode=ParseMode.HTML)
    else: await bot.send_message(chat,cap,reply_markup=menu_kb(st),parse_mode=ParseMode.HTML)
async def show(bot,chat,uid,s):
    st=load(uid); sc=SCENES[s]
    if sc['act']>st.get('unlock',1): await bot.send_message(chat,'Этот акт пока закрыт.',reply_markup=acts_kb(st)); return
    st['scene']=s; save(uid,st); head=f"<b>{s} — {html.escape(sc['title'])}</b>\n<i>Акт {sc['act']}</i>"
    img=BASE/'assets'/'images'/(sc.get('image') or '')
    if st.get('images') and sc.get('image') and img.exists(): await bot.send_photo(chat,FSInputFile(img),caption=head,parse_mode=ParseMode.HTML); await bot.send_message(chat,html.escape(sc['text']),reply_markup=scene_kb(sc),parse_mode=ParseMode.HTML)
    else: await bot.send_message(chat,head+'\n\n'+html.escape(sc['text']),reply_markup=scene_kb(sc),parse_mode=ParseMode.HTML)

async def start(m:Message,bot:Bot): await send_menu(bot,m.chat.id,m.from_user.id)
async def new(m:Message): save(m.from_user.id,default()); await m.answer('<b>Психопрофиль 1/3</b>\nЧто важнее, если всё пойдёт не по плану?',reply_markup=profile_kb(0),parse_mode=ParseMode.HTML)
async def cont(m:Message,bot:Bot): await show(bot,m.chat.id,m.from_user.id,load(m.from_user.id).get('scene') or 'SCENE_001')
async def note(m:Message):
    st=load(m.from_user.id); txt=m.text.partition(' ')[2].strip()
    if not txt: await m.answer('Напиши: /note твой вывод'); return
    st['notes'].append({'scene':st.get('scene'),'text':txt}); save(m.from_user.id,st); await m.answer('Записано.')
async def theory(m:Message):
    st=load(m.from_user.id); txt=m.text.partition(' ')[2].strip()
    if not txt: await m.answer('Напиши: /theory твоя версия'); return
    st['notes'].append({'scene':st.get('scene'),'text':'ТЕОРИЯ: '+txt}); save(m.from_user.id,st); await m.answer('Теория сохранена.')
async def admin(m:Message):
    if m.from_user.id in ADMINS: await m.answer('/goto SCENE_001\n/debug')
async def goto(m:Message,bot:Bot):
    if m.from_user.id not in ADMINS: return
    s=m.text.partition(' ')[2].strip().upper()
    if s in SCENES:
        st=load(m.from_user.id); st['unlock']=max(st.get('unlock',1),act(s)); save(m.from_user.id,st); await show(bot,m.chat.id,m.from_user.id,s)
async def debug(m:Message):
    if m.from_user.id in ADMINS: await m.answer('<pre>'+html.escape(json.dumps(load(m.from_user.id),ensure_ascii=False,indent=2)[:3500])+'</pre>',parse_mode=ParseMode.HTML)

async def cb_menu(q:CallbackQuery,bot:Bot):
    st=load(q.from_user.id); a=q.data.split(':')[1]
    if a=='home': await send_menu(bot,q.message.chat.id,q.from_user.id)
    elif a=='cont': await show(bot,q.message.chat.id,q.from_user.id,st.get('scene') or 'SCENE_001')
    elif a=='acts': await q.message.answer('Выберите акт:',reply_markup=acts_kb(st))
    elif a=='brief': await q.message.answer('Брифинг: найти пропавшую экспедицию и выяснить, почему объект снова подал сигнал.',reply_markup=menu_kb(st))
    elif a=='journal': await q.message.answer('\n'.join([x['text'] for x in st['notes'][-10:]]) or 'Журнал пуст.')
    elif a=='codex': await q.message.answer('\n'.join(st['docs'][-20:]) or 'Документов пока нет.')
    elif a=='map': await q.message.answer(f"Двор открыт. Внутренние сектора: {'открыты' if st.get('unlock',1)>=2 else 'закрыты'}. Архив: {'открыт' if st.get('unlock',1)>=3 else 'закрыт'}.")
    elif a=='set': st['images']=not st.get('images',True); save(q.from_user.id,st); await q.message.answer('Картинки переключены.',reply_markup=menu_kb(st))
    elif a=='note': await q.message.answer('Напиши /note вывод или /theory версия событий')
    await q.answer()
async def cb_act(q:CallbackQuery,bot:Bot):
    st=load(q.from_user.id); a=int(q.data.split(':')[1])
    if a>st.get('unlock',1): await q.answer('Акт закрыт',show_alert=True); return
    await show(bot,q.message.chat.id,q.from_user.id,{1:'SCENE_001',2:'SCENE_201',3:'SCENE_401'}[a]); await q.answer()
async def cb_prof(q:CallbackQuery,bot:Bot):
    st=load(q.from_user.id); _,step,val=q.data.split(':'); step=int(step); st['vars'][val]=st['vars'].get(val,0)+1; save(q.from_user.id,st)
    if step<2: await q.message.answer(f'<b>Психопрофиль {step+2}/3</b>\nВыберите реакцию.',reply_markup=profile_kb(step+1),parse_mode=ParseMode.HTML)
    else: await q.message.answer('Профиль сохранён. Ворота открываются.'); await show(bot,q.message.chat.id,q.from_user.id,'SCENE_001')
    await q.answer()
async def cb_choice(q:CallbackQuery,bot:Bot):
    _,s,i=q.data.split(':'); st=load(q.from_user.id)
    if st.get('scene')!=s: await q.answer('Этот выбор устарел',show_alert=True); return
    sc=SCENES[s]; c=sc['choices'][int(i)]; effects(st,c['effects']); st['history'].append([s,c['label']]); save(q.from_user.id,st)
    if s=='SCENE_120': await q.message.answer('Акт I завершён. Акт II открыт.',reply_markup=acts_kb(load(q.from_user.id)))
    elif s=='SCENE_380': await q.message.answer('Акт II завершён. Акт III открыт.',reply_markup=acts_kb(load(q.from_user.id)))
    elif not c['next']: await send_menu(bot,q.message.chat.id,q.from_user.id)
    else: await show(bot,q.message.chat.id,q.from_user.id,c['next'])
    await q.answer()

def health():
    class H(BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
        def log_message(self,*a): pass
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0',PORT),H).serve_forever(),daemon=True).start()
async def run():
    if not TOKEN: raise RuntimeError('BOT_TOKEN is not set')
    bot=Bot(TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML)); dp=Dispatcher()
    dp.message.register(start,CommandStart()); dp.message.register(new,Command('new')); dp.message.register(cont,Command('continue')); dp.message.register(start,Command('menu')); dp.message.register(note,Command('note')); dp.message.register(theory,Command('theory')); dp.message.register(admin,Command('admin')); dp.message.register(goto,Command('goto')); dp.message.register(debug,Command('debug'))
    dp.callback_query.register(cb_menu,F.data.startswith('m:')); dp.callback_query.register(cb_act,F.data.startswith('a:')); dp.callback_query.register(cb_prof,F.data.startswith('p:')); dp.callback_query.register(cb_choice,F.data.startswith('c:'))
    await dp.start_polling(bot)
def main():
    global SCENES
    dirs(); db(); make_images(); SCENES=build_scenes(); (BASE/'data').mkdir(exist_ok=True); (BASE/'data'/'scenes.generated.json').write_text(json.dumps({'count':len(SCENES)},ensure_ascii=False)); health(); asyncio.run(run())
if __name__=='__main__': main()
