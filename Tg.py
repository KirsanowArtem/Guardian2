# Обновлённый main.py с локализацией, исправленным запуском бота и шаблонизатором Bootstrap

import os
import json
import random
import string
import time
import threading
import asyncio
from flask import Flask, render_template, request, redirect, session, url_for
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask_babel import Babel, gettext as _

# === Конфигурация приложения ===
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['BABEL_DEFAULT_LOCALE'] = 'ru'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

babel = Babel(app)

LANGUAGES = ['ru', 'uk', 'en']

@babel.locale_selector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES)

# === Конфигурация бота ===
TOKEN = '8029722918:AAGg-WtEjL9aZiF35eO2rdmD9Z1RKTVHlN4'

# === Файлы данных ===
AUTH_CODES_FILE = 'auth_codes.json'
USERS_FILE = 'users.json'
GROUPS_FILE = 'groups.json'

for file in [AUTH_CODES_FILE, USERS_FILE, GROUPS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2, ensure_ascii=False)

# === Утилиты ===
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# === Telegram Bot ===
async def website_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    code = generate_code()
    expires = int(time.time()) + 300
    auth_codes = load_json(AUTH_CODES_FILE)
    auth_codes[user_id] = {"code": code, "expires": expires}
    save_json(AUTH_CODES_FILE, auth_codes)
    await update.message.reply_text(f"Ваш код для входа на сайт: {code}")

def run_bot():
    async def bot_main():
        app_telegram = ApplicationBuilder().token(TOKEN).build()
        app_telegram.add_handler(CommandHandler("website_auth", website_auth))
        await app_telegram.run_polling()

    asyncio.run(bot_main())

# === Flask Routes ===
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        telegram_id = request.form["telegram_id"]
        code = request.form["code"]
        auth_codes = load_json(AUTH_CODES_FILE)
        if telegram_id in auth_codes:
            auth = auth_codes[telegram_id]
            if auth["code"] == code and int(time.time()) < auth["expires"]:
                session["telegram_id"] = telegram_id
                return redirect("/register")
        return render_template("login.html", error=_("Неверный код или ID"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "telegram_id" not in session:
        return redirect("/")
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]
        email = request.form["email"]
        users = load_json(USERS_FILE)
        users[session["telegram_id"]] = {"login": login, "password": password, "email": email}
        save_json(USERS_FILE, users)
        return redirect("/groups")
    return render_template("register.html")

@app.route("/groups")
def groups():
    if "telegram_id" not in session:
        return redirect("/")
    groups_data = load_json(GROUPS_FILE)
    user_groups = groups_data.get(session["telegram_id"], {}).get("groups", [])
    for g in user_groups:
        g["count"] = len(g.get("members", []))
    return render_template("groups.html", groups=user_groups)

@app.route("/group/<int:group_id>")
def group_detail(group_id):
    if "telegram_id" not in session:
        return redirect("/")
    groups_data = load_json(GROUPS_FILE)
    user_groups = groups_data.get(session["telegram_id"], {}).get("groups", [])
    group = next((g for g in user_groups if g["id"] == group_id), None)
    if not group:
        return _("Группа не найдена"), 404
    return render_template("group_detail.html", group=group)

# === Запуск ===
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(debug=True, port=5000)
