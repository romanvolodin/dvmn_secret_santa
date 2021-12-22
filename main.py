import logging

from environs import Env
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)


def start(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=create_button_text)]]
    )
    update.message.reply_text(
        text="Организуй тайный обмен подарками, "
             "запусти праздничное настроение!",
        reply_markup=reply_markup,
    )
    return NAME  # к какому статусу перейти далее


def game_name_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Введите название игры:", reply_markup=ReplyKeyboardRemove()
    )
    return COST  # к какому статусу перейти далее


def cost_handler(update: Update, context: CallbackContext):
    game_name = update.message.text  # название игры, введенное пользователем
    print("Название игры", game_name)

    update.message.reply_text("Укажите стоимость:")
    return REG_DATE_LIMIT # к какому статусу перейти далее


def reg_date_handler(update: Update, context: CallbackContext):
    cost = update.message.text  # стоимость, введенная пользователем
    print("Стоимость подарка", cost)

    update.message.reply_text("Период регистрации участников:")
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s",
        level=logging.INFO
    )

    create_button_text = "Создать игру"

    # статусы
    NAME, COST, REG_DATE_LIMIT, SEND_DATE = range(4)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],  # выдается на старте при вводе /start
        states={
            # статусы
            NAME: [MessageHandler(Filters.text, game_name_handler)],
            COST: [MessageHandler(Filters.text, cost_handler)],
            REG_DATE_LIMIT: [MessageHandler(Filters.text, reg_date_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    updater.start_polling()  # Запуск бота
