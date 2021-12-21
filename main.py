import logging

import telegram

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater
from environs import Env


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Организуй тайный обмен подарками, "
                                  "запусти праздничное настроение!")


if __name__ == "__main__":
    env = Env()
    env.read_env()

    bot = telegram.Bot(token=env.str("BOT_TOKEN"))
    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    logging.basicConfig(
        format='%(levelname)s: %(asctime)s - %(name)s - %(message)s',
        level=logging.INFO)

    start_handler = CommandHandler('start', start) # При вводе /start вызов функции start
    dispatcher.add_handler(start_handler)

    updater.start_polling() # Запуск бота

    # updater.stop() # Остановить бота

