import telebot, json, time, random, os
from telebot.types import ReplyKeyboardMarkup
from openai import OpenAI
from gtts import gTTS
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
ADMINS={123456789}

bot=telebot.TeleBot(BOT_TOKEN)
client=OpenAI(api_key=API_KEY)

FILE="data.json"
try:
    data=json.load(open(FILE))
except:
    data={}

# ---------- база ----------

def save():
    json.dump(data,open(FILE,"w"))

def user(cid):
    return data.setdefault(str(cid),{
        "xp":0,"lvl":1,"coins":0,
        "mem":[],"notes":[],
        "hp":100,"last_daily":0
    })

# ---------- меню ----------

def kb():
    k=ReplyKeyboardMarkup(resize_keyboard=True)
    k.row("🤖 Чат","🖼 Картинка","🎙 Голос")
    k.row("📝 Заметка","🎮 RPG","🎁 Daily")
    k.row("👤 Профиль")
    return k

# ---------- механики ----------

def add_xp(u,n):
    u["xp"]+=n
    if u["xp"]>=u["lvl"]*60:
        u["xp"]=0
        u["lvl"]+=1
        u["coins"]+=25
        return True
    return False

def voice(chat_id,text):
    fn="v.mp3"
    gTTS(text=text[:200],lang="ru").save(fn)
    bot.send_voice(chat_id,open(fn,"rb"))
    os.remove(fn)

# ---------- старт ----------

@bot.message_handler(commands=["start"])
def start(m):
    user(m.chat.id)
    save()
    bot.send_message(m.chat.id,"v6 FINAL ⚡",reply_markup=kb())

# ---------- профиль ----------

@bot.message_handler(func=lambda m:m.text=="👤 Профиль")
def prof(m):
    u=user(m.chat.id)
    bot.reply_to(m,
        f"lvl {u['lvl']} xp {u['xp']}\n"
        f"coins {u['coins']}\nHP {u['hp']}")

# ---------- daily ----------

@bot.message_handler(func=lambda m:m.text=="🎁 Daily")
def daily(m):
    u=user(m.chat.id)
    if time.time()-u["last_daily"]<86400:
        bot.reply_to(m,"Уже получал")
        return
    u["coins"]+=30
    u["last_daily"]=time.time()
    save()
    bot.reply_to(m,"+30 монет")

# ---------- заметки ----------

@bot.message_handler(func=lambda m:m.text.startswith("📝"))
def note(m):
    text=m.text[1:].strip()
    if not text:
        bot.reply_to(m,"После 📝 напиши текст")
        return
    user(m.chat.id)["notes"].append(text)
    save()
    bot.reply_to(m,"Сохранено")

# ---------- RPG ----------

@bot.message_handler(func=lambda m:m.text=="🎮 RPG")
def rpg(m):
    u=user(m.chat.id)
    dmg=random.randint(5,25)
    u["hp"]-=dmg
    if u["hp"]<=0:
        u["hp"]=100
        u["coins"]+=20
        bot.reply_to(m,"⚔️ Бой выигран +20 монет")
    else:
        bot.reply_to(m,f"Тебя ударили на {dmg} HP")
    save()

# ---------- картинка ----------

@bot.message_handler(func=lambda m:m.text.startswith("🖼"))
def img(m):
    prompt=m.text[1:]
    try:
        r=client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="512x512"
        )
        bot.send_message(m.chat.id,r.data[0].url)
    except:
        bot.reply_to(m,"Ошибка генерации")

# ---------- антиспам ----------

last_time={}
def spam(cid):
    now=time.time()
    if now-last_time.get(cid,0)<1:
        return True
    last_time[cid]=now
    return False

# ---------- чат ИИ ----------

@bot.message_handler(func=lambda m: True)
def chat(m):
    cid=str(m.chat.id)
    if spam(cid): return
    if m.text in ["🤖 Чат","🎮 RPG","👤 Профиль","🎁 Daily"]:
        return

    u=user(cid)
    u["mem"].append({"role":"user","content":m.text})
    u["mem"]=u["mem"][-8:]

    try:
        r=client.responses.create(
            model="gpt-5-mini",
            input=u["mem"]
        )
        text=r.output_text
        u["mem"].append({"role":"assistant","content":text})

        if add_xp(u,6):
            bot.send_message(cid,"🎉 Level up")

        save()

        if m.text=="🎙 Голос":
            voice(cid,text)
        else:
            bot.reply_to(m,text)

    except:
        bot.reply_to(m,"Ошибка")

bot.infinity_polling()
