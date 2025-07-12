from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ВСТАВЬ СЮДА СВОЙ НОВЫЙ ТОКЕН
TOKEN = "8029722918:AAFaT_3I8wqfwfLJ8iWl-0h90WoGpBZxrJY"

groups = set()

async def handle_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        group_info = f"{chat.title} (ID: {chat.id})"
        if group_info not in groups:
            groups.add(group_info)
            print(f"Бот добавлен в группу: {group_info}")

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        if groups:
            await update.message.reply_text("Вот группы, где состоит бот:\n" + "\n".join(groups))
        else:
            await update.message.reply_text("Бот пока не состоит ни в одной группе.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle_group))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_command))

    print("Бот запущен.")
    app.run_polling()
