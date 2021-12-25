import datetime as dt
import logging

from environs import Env
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    ReplyMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.utils import helpers

from models import GameAdmin, Game, GameMember, User
from draw import manual_draw
from handlers.game import DEADLINE_OPTIONS, regex_for_date


admin_id = "введите свой id для теста"
button_cancel = "Отмена"


def games(update: Update, context: CallbackContext):
    bot = context.bot
    admins_games = Game.select().where(Game.created_by == admin_id)
    games_id_titles = [(game.game_link_id, game.title) for game in admins_games]
    update.message.reply_text("Игры, в которых вы админ:")
    for game_id, game_title in games_id_titles:
        ### Здесь выдаст ссылку на себя
        # deep_link = helpers.create_deep_linked_url(bot.username, game_id)

        ### Здесь выдаст ссылку на другого бота DvmnSecretSantaAdminBot
        deep_link = helpers.create_deep_linked_url("DvmnSecretSantaAdminBot", game_id)
        update.message.reply_text(f"{game_title}: {deep_link}")


def start(update: Update, context: CallbackContext):
    # TODO Добавить инструкцию по командам для пользователя
    if context.args:
        context.user_data["current_game_id"] = context.args[0]
        # Вывести список участников игры
        dispatcher.add_handler(
            CommandHandler(
                "members", show_members, Filters.user(user_id=admin_id), pass_args=True
            )
        )
        # Перейти к ручной жеребьевке
        dispatcher.add_handler(
            CommandHandler(
                "draw", ask_for_draw, Filters.user(user_id=admin_id), pass_args=True
            )
        )
        # Изменить параметры игры
        dispatcher.add_handler(
            CommandHandler(
                "edit", edit_game, Filters.user(user_id=admin_id), pass_args=True
            )
        )


def show_members(update: Update, context: CallbackContext):
    game = get_game_by_id(context.user_data["current_game_id"])
    game_members = GameMember.select().where(GameMember.game_id == game.id)

    update.message.reply_text(f"Участники игры {game.title}:")
    available_user_ids = []
    for member in game_members:
        user_form = User.get_by_id(member.user_id)
        update.message.reply_text(
            f"id:{member.id}\n" f"{user_form.name}, email: {user_form.email}"
        )
        available_user_ids.append(member.id)
    context.user_data["available_user_ids"] = available_user_ids
    update.message.reply_text(
        "Чтобы удалить участника введите команду /delete и id участника.\n\n"
        "Например: /delete 15"
    )
    dispatcher.add_handler(
        CommandHandler("delete", call_delete_member, Filters.user(user_id=admin_id))
    )


def call_delete_member(update: Update, context: CallbackContext):
    # TODO обработать IndexError, если юзер не укажет id
    if not context.args[0].isdigit():
        update.message.reply_text("Введите корректный id. Например: /delete 15")
    else:
        user_id_to_delete = int(context.args[0])
        if user_id_to_delete in context.user_data["available_user_ids"]:
            keyboard = [
                [InlineKeyboardButton("Удалить", callback_data=f"{user_id_to_delete}")],
                [InlineKeyboardButton(button_cancel, callback_data=button_cancel)],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text=f"Удалить участника с id {user_id_to_delete}?",
                reply_markup=reply_markup,
            )
            updater.dispatcher.add_handler(CallbackQueryHandler(delete_member))
        else:
            update.message.reply_text(
                text=f"Пользователя с id {user_id_to_delete} не найдено в базе"
            )


def delete_member(update: Update, context: CallbackContext):
    callback_query = update.callback_query.data
    if callback_query == button_cancel:
        pass
        # TODO добавить обработку отмены операции
    else:
        user_id_to_delete = callback_query
        GameMember.delete_by_id(user_id_to_delete)
        # TODO добавить сообщение, что пользователь удален


def ask_for_draw(update: Update, context: CallbackContext):
    game = get_game_by_id(context.user_data["current_game_id"])
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Провести жеребьевку", callback_data="1")],
            [InlineKeyboardButton(button_cancel, callback_data="0")],
        ]
    )
    update.message.reply_text(
        text=f"Провеcти жеребьевку для игры {game.title}",
        reply_markup=reply_markup,
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(make_draw))


def make_draw(update: Update, context: CallbackContext):
    callback_query = update.callback_query.data
    if callback_query == "1":
        manual_draw(context.user_data["current_game_id"])
    else:
        update.message.reply_text(text="Отмена")


def edit_game(update: Update, context: CallbackContext):
    game = get_game_by_id(context.user_data["current_game_id"])
    keyboard = [
        [
            InlineKeyboardButton("Название", callback_data="title"),
            InlineKeyboardButton("Стоимость подарка", callback_data="budget"),
        ],
        [
            InlineKeyboardButton("Период регистрации", callback_data="deadline"),
            InlineKeyboardButton("Дату отправки подарка", callback_data="send_date"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text=f"Изменить игру {game.title}:\n\n"
        f"Ограничение стоимости подарка: {game.budget}\n"
        f"Регистрация до: {game.deadline.strftime('%d.%m.%Y, %H:%M(МСК)')}\n"
        f"Дата отправки подарков: {game.gift_send_date.strftime('%d.%m.%Y')}\n\n"
        f"Что изменить?",
        reply_markup=reply_markup,
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_game_edit))


def handle_game_edit(update: Update, context: CallbackContext):
    query = update.callback_query
    query_value = update.callback_query.data
    query.answer()
    if query_value == "title":
        query.edit_message_text(text=f"Укажите новое название:")
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, edit_game_name, pass_user_data=True)
        )
    elif query_value == "budget":
        # TODO пока работает только ввод строки без выбора вариантов
        query.edit_message_text(text=f"Выберите новый бюджет:")
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, edit_game_budget, pass_user_data=True)
        )
    elif query_value == "deadline":
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(DEADLINE_OPTIONS[0], callback_data="first"),
                    InlineKeyboardButton(DEADLINE_OPTIONS[1], callback_data="second"),
                ],
            ]
        )
        query.edit_message_text(
            text=f"Выберите новый период регистрации:", reply_markup=reply_markup
        )
        # TODO Здесь пока не работает
        updater.dispatcher.add_handler(CallbackQueryHandler(edit_game_deadline))

    elif query_value == "send_date":
        query.edit_message_text(
            text=f"Укажите новую дату отправки подарка в формате 13.01.2022:"
        )
        updater.dispatcher.add_handler(
            MessageHandler(
                Filters.regex(regex_for_date), edit_game_send_date, pass_user_data=True
            )
        )


def edit_game_name(update: Update, context: CallbackContext):
    new_name = update.message.text
    game = get_game_by_id(context.user_data["current_game_id"])
    game.title = new_name
    game.save()
    update.message.reply_text(text="Ок. Название игры изменено")


def edit_game_budget(update: Update, context: CallbackContext):
    # TODO пока работает только ввод строки без выбора вариантов
    new_budget = update.message.text
    game = get_game_by_id(context.user_data["current_game_id"])
    game.budget = new_budget
    game.save()
    update.message.reply_text(text="Ок. Стоимость подарка изменена")


def edit_game_deadline(update: Update, context: CallbackContext):
    print(update.message.text)
    # TODO пока не работает
    print("Game id", context.user_data["current_game_id"])
    query = update.callback_query
    query_value = update.callback_query.data
    print("query_value", query_value)
    query.answer()
    if query_value == DEADLINE_OPTIONS[0]:
        new_deadline = dt.datetime(2021, 12, 25, hour=12)
    else:
        new_deadline = dt.datetime(2021, 12, 31, hour=12)

    game = Game.get(Game.game_link_id == context.user_data["current_game_id"])
    game.deadline = new_deadline
    game.save()
    query.edit_message_text(text="Ок. Период регистрации изменен")


def edit_game_send_date(update: Update, context: CallbackContext):
    try:
        new_send_date = dt.datetime.strptime(update.message.text, "%d.%m.%Y")
    except ValueError:
        update.message.reply_text(
            text="Упс. Что-то пошло не так. Введите дату в формате 15.01.2022:"
        )

    game = Game.get(Game.game_link_id == context.user_data["current_game_id"])
    game.gift_send_date = new_send_date
    game.save()
    update.message.reply_text(text="Ок. Дата отправки подарка изменена")


def get_game_by_id(game_id):
    return Game.get(Game.game_link_id == game_id)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s", level=logging.INFO
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    # Изначально доступны только эти команды. Пользователь вводит /games
    # Переходит по ссылке в def start() уже с id игры
    dispatcher.add_handler(
        CommandHandler("games", games, Filters.user(user_id=admin_id))
    )
    dispatcher.add_handler(
        CommandHandler("start", start, Filters.user(user_id=admin_id))
    )

    updater.start_polling()
    updater.idle()
