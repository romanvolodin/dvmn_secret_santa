import datetime
import logging

from environs import Env
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    Updater
)

from admin import admin_main
from db_helpers import create_db
from draw import make_draw
from handlers.conversation import conversation_handler
from models import Game


def admin(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Введите команду /games, чтобы посмотреть игры, в которых у вас права админа",
    )
    admin_main(bot_token, updater, dispatcher)


def main():
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s", level=logging.INFO
    )
    global bot_token
    global updater
    global dispatcher

    bot_token = env.str("BOT_TOKEN")
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(CommandHandler("admin", admin, Filters.all))

    msk_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    games = Game.select()
    for game in games:
        if game.deadline == msk_time:
            make_draw(game.game_link_id, bot_token)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    create_db()
    main()
