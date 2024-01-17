import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, Updater, filters
# import validators
import requests

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter animals or adopters by enter (new line)")
#
# async def adoptation(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     msg = Update.message.text
#     if msg == "animals":
#         result = requests.get_json('http://127.0.0.1:8000/adoptation/animals/')
#     elif msg == "adopters":
#         result = requests.get('http://127.0.0.1:8000/adoptation/adopters/')
#         await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
#
#
# if __name__ == '__main__':
#     application = ApplicationBuilder().token('6981259613:AAHZFExFf3b08tdL0R5rJEPt6W315dh-uXw').build()
#
#     start_handler = CommandHandler('start', start)
#     application.add_handler(start_handler)
#     message_handler = MessageHandler(TEXT, adoptation)
#     application.add_handler(message_handler)
#     application.run_polling()


# def start(update, context):
#     user_name = update.message.from_user.username
#     update.message.reply_text(f" hello , i am a {user_name} bot, you want see animals or adopters?(Enter new line)")
#
# def main():
#     updater = Updater("6981259613:AAHZFExFf3b08tdL0R5rJEPt6W315dh-uXw", use_context=True)
#     dp = updater.dispatcher
#
#     dp.add_handler(CommandHandler("start", start))
#
#     updater.start_polling()
#     updater.idle()
#
# if __name__ == '__main__':
#     main()

cache = {}
ADOPTER_NAME, SSN, SAVE_OR_CANCEL = range(3)

cache_2 = {}
ANIMAL_NAME, age, type, save_or_cancel = range(4)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = context.bot.username
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"hello , I am {user_name}, you want see animals or adopters?(Enter new line)")

async def get_animals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = "http://127.0.0.1:8000/adoptation/animals/"
    response = requests.get(api_url)

    if response.status_code == 200:
        animals = response.json()
        result = ""
        for animal in animals:
            result += f"name: {animal['name']}, age: {animal['age']}, type: {animal['type']}, adopted: {animal['adopted']}\n"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"invalid {response.status_code}")

async def get_adopters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = "http://127.0.0.1:8000/adoptation/adopters/"
    response = requests.get(api_url)

    if response.status_code == 200:
        adopters = response.json()
        result = ""
        for adopter in adopters:
            result += f"name: {adopter['name']}, ssn: {adopter['ssn']}\n"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"invalid {response.status_code}")

async def add_adopter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache
    user_id = update.message.from_user.id
    cache[user_id] = {
        "adopter": {}
    }
    await update.message.reply_text("""Please enter name and ssn in separate messages in the follwing format:
name: john
ssn: 1234567890""")
    return ADOPTER_NAME

async def get_adopter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache
    user_id = update.message.from_user.id
    cache[user_id]["adopter"]["name"] = update.message.text.split(":")[1].strip()
    await update.message.reply_text(f'Entered name successfully: {cache[user_id]["adopter"]["name"]}')
    await update.message.reply_text("Please enter ssn in the follwing format:\nssn: 1234567890")
    return SSN

async def get_ssn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache
    user_id = update.message.from_user.id
    cache[user_id]["adopter"]["ssn"] = update.message.text.split(":")[1].strip()
    await update.message.reply_text(f'Entered ssn successfully: {cache[user_id]["adopter"]["ssn"]}')
    await update.message.reply_text("Please enter save to save or cancel to cancel")
    return SAVE_OR_CANCEL

async def save_or_cancel_adopter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache
    cancel_or_save = update.message.text
    if cancel_or_save == "save":
        session = requests.Session()
        response = session.get("http://127.0.0.1:8000/api-auth/login/")
        if 'csrftoken' in session.cookies:
            csrftoken = session.cookies['csrftoken']
        else:
            csrftoken = session.cookies['csrf']
        response = session.post("http://127.0.0.1:8000/api-auth/login/", data={"username": "baran", "password": "123456789", "csrfmiddlewaretoken": csrftoken})
        csrftoken = session.cookies['csrftoken']
        user_id = update.message.from_user.id
        adopter = cache[user_id]["adopter"]
        api_url = "http://127.0.0.1:8000/adoptation/adopters/"
        session.headers.update({"X-Csrftoken": csrftoken})
        response = session.post(api_url, json=adopter)

        if response.status_code == 201:
            await update.message.reply_text('Adopter saved successfully')
        else:
            await update.message.reply_text(f'Error: {response.status_code}')
        session.close()
        del cache[user_id]
    else:
        user_id = update.message.from_user.id
        del cache[user_id]
        await update.message.reply_text('Adding adopter canceled successfully')
    return ConversationHandler.END

async def cancel_adopter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache
    user_id = update.message.from_user.id
    del cache[user_id]
    await update.message.reply_text('Adding adopter canceled successfully')
    return ConversationHandler.END

async def add_animal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache_2
    user_id = update.message.from_user.id
    cache[user_id] = {
        "animal": {}
    }
    await update.message.reply_text("""Please enter name and age and type in separate messages in the follwing format:
name: alex
age: 1
type: dog or cat""")
    return ANIMAL_NAME

async def get_animal_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache_2
    user_id = update.message.from_user.id
    cache[user_id]["animal"]["name"] = update.message.text.split(":")[1].strip()
    await update.message.reply_text(f'Entered name successfully: {cache[user_id]["animal"]["name"]}')
    await update.message.reply_text("Please enter age in the follwing format:\nage: 1")
    return age

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global cache_2
    user_id = update.message.from_user.id
    cache[user_id]["animal"]["ssn"] = update.message.text.split(":")[1].strip()
    await update.message.reply_text(f'Entered age successfully: {cache[user_id]["animal"]["age"]}')
    await update.message.reply_text("Please enter you'r animal type")
    return


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    application = ApplicationBuilder().token('6981259613:AAHZFExFf3b08tdL0R5rJEPt6W315dh-uXw').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("animals", get_animals))
    application.add_handler(CommandHandler("adopters", get_adopters))

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("add_adopter", add_adopter)],
            states={
                ADOPTER_NAME: [MessageHandler(filters.Regex("^name:(.*)$"), get_adopter_name)],
                SSN: [MessageHandler(filters.Regex("^ssn:[ ]?([0-9]{10})$"), get_ssn)],
                SAVE_OR_CANCEL: [MessageHandler(filters.Regex("^(save|cancel)$"), save_or_cancel_adopter)],
                ANIMAL_NAME: [MessageHandler(filters.Regex("^name:(.*)$"), get_animal_name)],
                age: [MessageHandler(filters.Regex("^age:[ ]?([1-9]{2})$"), get_age)],

            },
            fallbacks=[CommandHandler("cancel_adopter", cancel_adopter)]
        )
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
