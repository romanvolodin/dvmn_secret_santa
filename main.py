import datetime as dt
import logging
import uuid

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
from telegram.utils import helpers

from models import Game, User, GameAdmin


BUDGET_OPTIONS = [
        "Нет",
        "до 500 руб",
        "500-1000 руб",
        "1000-2000 руб"
    ]
DEADLINE_OPTIONS = [
        "до 25.12.2021",
        "до 31.12.2021"
    ]
regex_for_date = r"\d{1,2}.\d{1,2}.2022"


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
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUDGET_OPTIONS[0]),
                KeyboardButton(text=BUDGET_OPTIONS[1]),
             ],
            [
                KeyboardButton(text=BUDGET_OPTIONS[2]),
                KeyboardButton(text=BUDGET_OPTIONS[3]),
            ]
        ]
    )
    update.message.reply_text(
        text="Ограничение стоимости подарка:",
        reply_markup=reply_markup,
    )
    return DEADLINE  # к какому статусу перейти далее


def deadline_handler(update: Update, context: CallbackContext):
    context.user_data["budget"] = update.message.text  # стоимость, введенная пользователем
    print("Стоимость подарка", context.user_data["budget"])
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=DEADLINE_OPTIONS[0]),
                KeyboardButton(text=DEADLINE_OPTIONS[1]),
            ]
        ]
    )
    update.message.reply_text(
        text="Период регистрации участников:",
        reply_markup=reply_markup,
    )
    return SEND_DATE


def send_date_handler(update: Update, context: CallbackContext):
    if update.message.text == DEADLINE_OPTIONS[0]:
        context.user_data["deadline"] = dt.datetime(2021, 12, 25, hour=12)
    else:
        context.user_data["deadline"] = dt.datetime(2021, 12, 31, hour=12)
    print("Дедлайн", context.user_data["deadline"])

    update.message.reply_text(
        text="Дата отправки подарка (например 15.01.2022):",
        reply_markup=ReplyKeyboardRemove()
    )
    return FINISH


def finish_handler(update: Update, context: CallbackContext):
    try:
        context.user_data["send_date"] = dt.datetime.strptime(
            update.message.text, "%d.%m.%Y"
        )
    except ValueError:
        update.message.reply_text(
            text="Упс. Что-то пошло не так. Введите дату формате 15.01.2022:"
        )
        return FINISH
    print("Отправка", context.user_data["send_date"])
    print(context.user_data)

    user, is_created = User.get_or_create(id=update.message.from_user.id)
    bot = context.bot
    deep_link_payload = str(uuid.uuid4())[:8]
    deep_link = helpers.create_deep_linked_url(bot.username, deep_link_payload)

    game_title = context.user_data["game_title"]

    game = Game.create(
        reg_link=deep_link_payload,
        title=game_title,
        budget=context.user_data["budget"],
        deadline=context.user_data["deadline"],
        gift_send_date=context.user_data["send_date"],
        created_by=user,
    )
    GameAdmin.create(
        user=user,
        game=game,
    )
    update.message.reply_text("Отлично, Тайный Санта уже готовится "
                              "к раздаче подарков!")
    update.message.reply_text(f'Ссылка для регистрации в игре "{game_title}": '
                              f'{deep_link}')
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
                MessageHandler(Filters.regex(create_button_text),
                               game_title_handler,
                               pass_user_data=True)
            ],
            BUDGET: [
                MessageHandler(Filters.text ^ Filters.command,
                               budget_handler,
                               pass_user_data=True)
            ],
            DEADLINE: [
                MessageHandler(Filters.regex(f"^({BUDGET_OPTIONS[0]}|"
                                             f"{BUDGET_OPTIONS[1]}|"
                                             f"{BUDGET_OPTIONS[2]}|"
                                             f"{BUDGET_OPTIONS[3]})$"),
                               deadline_handler,
                               pass_user_data=True)
            ],
            SEND_DATE: [
                MessageHandler(Filters.regex(f"^({DEADLINE_OPTIONS[0]}|"
                                             f"{DEADLINE_OPTIONS[1]})$"),
                               send_date_handler,
                               pass_user_data=True)
            ],
            FINISH: [
                MessageHandler(Filters.regex(regex_for_date) | Filters.command,
                               finish_handler,
                               pass_user_data=True)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    updater.start_polling()  # Запуск бота
