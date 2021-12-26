import logging

from environs import Env
from telegram.ext import Updater

from db_helpers import create_db
from handlers.conversation import conversation_handler


def main():
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s", level=logging.INFO
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    create_db()
    main()
