import datetime as dt
import uuid

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
)
from telegram.utils import helpers

from models import Game, User, GameAdmin

GET_TITLE, GET_BUDGET, GET_DEADLINE, GET_SEND_DATE, GET_FINISH = range(5)
create_button_text = "Создать игру"
BUDGET_OPTIONS = ["Нет", "до 500 руб", "500-1000 руб", "1000-2000 руб"]
DEADLINE_OPTIONS = ["до 25.12.2021", "до 31.12.2021"]
regex_for_date = r"\d{1,2}.\d{1,2}.2022"


def game_title_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Введите название игры:", reply_markup=ReplyKeyboardRemove()
    )
    return GET_BUDGET


def budget_handler(update: Update, context: CallbackContext):
    context.user_data["game_title"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUDGET_OPTIONS[0]),
                KeyboardButton(text=BUDGET_OPTIONS[1]),
            ],
            [
                KeyboardButton(text=BUDGET_OPTIONS[2]),
                KeyboardButton(text=BUDGET_OPTIONS[3]),
            ],
        ]
    )
    update.message.reply_text(
        text="Ограничение стоимости подарка:",
        reply_markup=reply_markup,
    )
    return GET_DEADLINE


def deadline_handler(update: Update, context: CallbackContext):
    context.user_data["budget"] = update.message.text
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
    return GET_SEND_DATE


def send_date_handler(update: Update, context: CallbackContext):
    if update.message.text == DEADLINE_OPTIONS[0]:
        context.user_data["deadline"] = dt.datetime(2021, 12, 25, hour=12)
    else:
        context.user_data["deadline"] = dt.datetime(2021, 12, 31, hour=12)

    update.message.reply_text(
        text="Дата отправки подарка (например 15.01.2022):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_FINISH


def finish_handler(update: Update, context: CallbackContext):
    try:
        context.user_data["send_date"] = dt.datetime.strptime(
            update.message.text, "%d.%m.%Y"
        )
    except ValueError:
        update.message.reply_text(
            text="Упс. Что-то пошло не так. Введите дату в формате 15.01.2022:"
        )
        return GET_FINISH

    user, is_created = User.get_or_create(id=update.message.from_user.id)
    bot = context.bot
    deep_link_payload = str(uuid.uuid4())[:8]
    deep_link = helpers.create_deep_linked_url(bot.username, deep_link_payload)

    game_title = context.user_data["game_title"]

    game = Game.create(
        game_link_id=deep_link_payload,
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
    update.message.reply_text("Отлично, Тайный Санта уже готовится к раздаче подарков!")
    update.message.reply_text(
        f'Ссылка для регистрации в игре "{game_title}": {deep_link}'
    )
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена создания игры")
    return ConversationHandler.END
