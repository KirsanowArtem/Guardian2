import json
import os
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from telegram import Update, Bot, Chat, ChatMember, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import asyncio
from threading import Thread
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
BOT_TOKEN = '8029722918:AAFaT_3I8wqfwfLJ8iWl-0h90WoGpBZxrJY'
SECRET_CODE_LENGTH = 8


# Инициализация данных
def init_data():
    os.makedirs('data', exist_ok=True)
    defaults = {
        'users.json': {"users": [], "auth_codes": {}},
        'groups.json': {"groups": []},
        'members.json': {},
        'mutes.json': {},
        'bans.json': {},
        'settings.json': {},
        'credentials.json': {"users": {}},
        'access_codes.json': {}
    }

    for filename, data in defaults.items():
        if not os.path.exists(f'data/{filename}'):
            with open(f'data/{filename}', 'w') as f:
                json.dump(data, f, indent=4)


init_data()


# Функции для работы с данными
def load_data(filename):
    with open(f'data/{filename}', 'r') as f:
        return json.load(f)


def save_data(data, filename):
    with open(f'data/{filename}', 'w') as f:
        json.dump(data, f, indent=4)


def generate_auth_code(user_id):
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(SECRET_CODE_LENGTH))
    data = load_data('users.json')
    data['auth_codes'][str(user_id)] = {
        'code': code,
        'used': False
    }
    save_data(data, 'users.json')
    return code


def generate_access_code(user_id):
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    data = load_data('access_codes.json')
    data[code] = str(user_id)
    save_data(data, 'access_codes.json')
    return code


def get_user_by_access_code(code):
    data = load_data('access_codes.json')
    return data.get(code)


async def save_group_info(bot, chat):
    """Сохраняем информацию о группе"""
    groups_data = load_data('groups.json')
    group_exists = False

    # Проверяем, есть ли уже такая группа
    for group in groups_data['groups']:
        if group['id'] == chat.id:
            group_exists = True
            # Обновляем данные
            group['name'] = chat.title
            group['member_count'] = await bot.get_chat_member_count(chat.id)
            if hasattr(chat, 'photo') and chat.photo:  # Проверяем наличие фото
                group['photo'] = (await chat.photo.get_big_file()).file_path
            break

    if not group_exists:
        # Добавляем новую группу
        photo_path = None
        if hasattr(chat, 'photo') and chat.photo:  # Проверяем наличие фото
            photo_path = (await chat.photo.get_big_file()).file_path

        new_group = {
            'id': chat.id,
            'name': chat.title,
            'type': chat.type,
            'member_count': await bot.get_chat_member_count(chat.id),
            'photo': photo_path
        }
        groups_data['groups'].append(new_group)

    save_data(groups_data, 'groups.json')

async def update_group_members(bot, chat_id):
    """Обновляем список участников группы"""
    members_data = load_data('members.json')
    if str(chat_id) not in members_data:
        members_data[str(chat_id)] = []

    # Получаем всех участников
    async for member in bot.get_chat_members(chat_id):
        user = member.user
        photos = await user.get_profile_photos(limit=1)
        photo_path = photos.photos[0][-1].file_path if photos.total_count > 0 else None

        member_info = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'photo': photo_path,
            'can_write': True  # По умолчанию разрешено писать
        }

        # Проверяем, есть ли уже такой участник
        existing_member = next((m for m in members_data[str(chat_id)] if m['id'] == user.id), None)
        if not existing_member:
            members_data[str(chat_id)].append(member_info)
        else:
            # Обновляем данные существующего участника
            existing_member.update(member_info)

    save_data(members_data, 'members.json')


async def handle_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех событий"""
    if update.message:
        chat = update.message.chat
    elif update.my_chat_member:
        chat = update.my_chat_member.chat
    else:
        return

    if chat.type in ["group", "supergroup"]:
        await save_group_info(context.bot, chat)
        await update_group_members(context.bot, chat.id)
        print(f"Обновлена информация о группе: {chat.title}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для управления группами.\n"
        "Используй /website_auth для кода привязки к сайту.\n"
        "Используй /my_groups для списка групп."
    )


async def website_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    code = generate_auth_code(user_id)

    await update.message.reply_text(
        f"🔑 Ваш код привязки: {code}\n\n"
        f"1. Перейдите на сайт\n"
        f"2. Нажмите 'Зарегистрироваться'\n"
        f"3. Введите этот код"
    )


async def my_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки групп в Telegram"""
    groups_data = load_data('groups.json')
    if groups_data['groups']:
        response = "Группы с ботом:\n\n" + "\n".join(
            f"{g['name']} (ID: {g['id']})" for g in groups_data['groups']
        )
    else:
        response = "Бот не в группах. Добавьте бота в группу и отправьте любое сообщение."
    await update.message.reply_text(response)


@app.route('/')
def index():
    if 'user_id' in session:
        if 'access_code' not in session:
            session['access_code'] = generate_access_code(session['user_id'])
        return redirect(f"/groups/{session['access_code']}")
    return render_template('index.html')


@app.route('/groups/<access_code>')
def show_groups(access_code):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = get_user_by_access_code(access_code)
    if not user_id or str(session.get('user_id')) != user_id:
        return redirect(url_for('login'))

    groups_data = load_data('groups.json')
    return render_template('groups.html',
                           groups=groups_data['groups'],
                           access_code=access_code)


@app.route('/group/<int:group_id>')
def group_management(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    tab = request.args.get('tab', 'members')
    groups_data = load_data('groups.json')
    group = next((g for g in groups_data['groups'] if g['id'] == group_id), None)

    if not group:
        return "Группа не найдена", 404

    members_data = load_data('members.json').get(str(group_id), [])
    mutes_data = load_data('mutes.json').get(str(group_id), {})
    bans_data = load_data('bans.json').get(str(group_id), {})

    # Добавляем информацию о мутах и банах к участникам
    for member in members_data:
        member['is_muted'] = str(member['id']) in mutes_data
        member['is_banned'] = str(member['id']) in bans_data

    return render_template('group_management.html',
                           group=group,
                           members=members_data,
                           tab=tab,
                           BOT_TOKEN=BOT_TOKEN)


@app.route('/api/mute_user', methods=['POST'])
def mute_user():
    data = request.get_json()
    group_id = data['group_id']
    user_id = data['user_id']
    reason = data.get('reason', '')
    duration = int(data.get('duration', 3600))  # По умолчанию 1 час

    mutes = load_data('mutes.json')
    if str(group_id) not in mutes:
        mutes[str(group_id)] = {}

    mutes[str(group_id)][str(user_id)] = {
        'until': (datetime.now() + timedelta(seconds=duration)).isoformat(),
        'reason': reason
    }

    save_data(mutes, 'mutes.json')
    return jsonify({'status': 'success'})


@app.route('/api/unmute_user', methods=['POST'])
def unmute_user():
    data = request.get_json()
    group_id = data['group_id']
    user_id = data['user_id']

    mutes = load_data('mutes.json')
    if str(group_id) in mutes and str(user_id) in mutes[str(group_id)]:
        del mutes[str(group_id)][str(user_id)]
        save_data(mutes, 'mutes.json')

    return jsonify({'status': 'success'})


@app.route('/api/ban_user', methods=['POST'])
def ban_user():
    data = request.get_json()
    group_id = data['group_id']
    user_id = data['user_id']
    reason = data.get('reason', '')

    bans = load_data('bans.json')
    if str(group_id) not in bans:
        bans[str(group_id)] = {}

    bans[str(group_id)][str(user_id)] = {
        'banned_at': datetime.now().isoformat(),
        'reason': reason
    }

    save_data(bans, 'bans.json')
    return jsonify({'status': 'success'})


@app.route('/api/unban_user', methods=['POST'])
def unban_user():
    data = request.get_json()
    group_id = data['group_id']
    user_id = data['user_id']

    bans = load_data('bans.json')
    if str(group_id) in bans and str(user_id) in bans[str(group_id)]:
        del bans[str(group_id)][str(user_id)]
        save_data(bans, 'bans.json')

    return jsonify({'status': 'success'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        creds = load_data('credentials.json')
        user_data = creds['users'].get(username)

        if user_data and check_password_hash(user_data['password'], password):
            session['user_id'] = user_data['telegram_id']
            session['access_code'] = generate_access_code(user_data['telegram_id'])
            return redirect(f"/groups/{session['access_code']}")

        return render_template('login.html', error="Неверный логин или пароль")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        auth_code = request.form['auth_code']
        username = request.form['username']
        password = request.form['password']

        users_data = load_data('users.json')
        user_id = None

        for uid, code_data in users_data['auth_codes'].items():
            if code_data['code'] == auth_code and not code_data['used']:
                user_id = uid
                users_data['auth_codes'][uid]['used'] = True
                save_data(users_data, 'users.json')
                break

        if not user_id:
            return render_template('register.html', error="Неверный код или код уже использован")

        creds = load_data('credentials.json')
        if username in creds['users']:
            return render_template('register.html', error="Этот логин уже занят")

        creds['users'][username] = {
            'password': generate_password_hash(password),
            'telegram_id': user_id
        }
        save_data(creds, 'credentials.json')

        session['user_id'] = user_id
        session['access_code'] = generate_access_code(user_id)

        return redirect(f"/groups/{session['access_code']}")

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


async def run_bot():
    """Запуск Telegram бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("website_auth", website_auth))
    application.add_handler(CommandHandler("my_groups", my_groups))
    application.add_handler(MessageHandler(filters.ALL, handle_all_updates))

    # Инициализация (без попытки загрузить группы при старте)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("Бот запущен! Добавьте его в группу и отправьте любое сообщение.")

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await application.stop()
        await application.shutdown()


if __name__ == '__main__':
    bot_thread = Thread(target=lambda: asyncio.run(run_bot()))
    bot_thread.daemon = True
    bot_thread.start()

    app.run(port=5000, debug=True, use_reloader=False)