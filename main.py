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
    return TITLE  # к какому статусу перейти далее


def game_title_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Введите название игры:", reply_markup=ReplyKeyboardRemove()
    )
    return BUDGET  # к какому статусу перейти далее


def budget_handler(update: Update, context: CallbackContext):
    context.user_data["game_title"] = update.message.text  # название игры, введенное пользователем
    print("Название игры", context.user_data["game_title"])

    update.message.reply_text("Укажите стоимость:")
    return DEADLINE  # к какому статусу перейти далее


def deadline_handler(update: Update, context: CallbackContext):
    context.user_data["budget"] = update.message.text  # стоимость, введенная пользователем
    print("Стоимость подарка", context.user_data["budget"])

    update.message.reply_text("Период регистрации участников:")
    return SEND_DATE


def send_date_handler(update: Update, context: CallbackContext):
    context.user_data["deadline"] = update.message.text
    print("Дедлайн", context.user_data["deadline"])

    update.message.reply_text("Дата отправки подарка:")
    return FINISH


def finish_handler(update: Update, context: CallbackContext):
    context.user_data["send_date"] = update.message.text
    print("Отправка", context.user_data["send_date"])
    update.message.reply_text("Отлично, Тайный Санта уже готовится "
                              "к раздаче подарков!")
    print(context.user_data)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена создания игры")
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
    TITLE, BUDGET, DEADLINE, SEND_DATE, FINISH = range(5)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],  # выдается на старте при вводе /start
        states={
            # статусы
            TITLE: [
                MessageHandler(Filters.text ^ Filters.command, game_title_handler,
                               pass_user_data=True)
            ],
            BUDGET: [
                MessageHandler(Filters.text ^ Filters.command, budget_handler,
                               pass_user_data=True)
            ],
            DEADLINE: [
                MessageHandler(Filters.text ^ Filters.command, deadline_handler,
                               pass_user_data=True)
            ],
            SEND_DATE: [
                MessageHandler(Filters.text ^ Filters.command, send_date_handler,
                               pass_user_data=True)
            ],
            FINISH: [
                MessageHandler(Filters.text | Filters.command, finish_handler,
                               pass_user_data=True)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    updater.start_polling()  # Запуск бота
