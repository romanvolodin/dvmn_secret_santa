import datetime as dt
import logging

from environs import Env
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

from models import GameAdmin, Game, GameMember, User
from draw import manual_draw
from handlers.game import BUDGET_OPTIONS, DEADLINE_OPTIONS, regex_for_date

INITIAL_CHOICE = range(1)

button_cancel = "Отмена"


def games(update: Update, context: CallbackContext):
    user = User.get_by_id(update.effective_user.idd)
    keyboard = []
    for game in user.created_games:
        keyboard.append(
            [InlineKeyboardButton(game.title, callback_data=game.game_link_id)]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Игры, в которых вы админ:",
        reply_markup=reply_markup,
    )


def show_game(update: Update, context: CallbackContext):
    query = update.callback_query
    chosen_game_id = query.data
    game = get_game_by_id(chosen_game_id)
    context.user_data["current_game_id"] = chosen_game_id

    keyboard = [
        [
            InlineKeyboardButton("Показать участников", callback_data="members"),
            InlineKeyboardButton("Изменить", callback_data="edit"),
        ],
        [
            InlineKeyboardButton("Провести жеребьевку", callback_data="draw"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        text=f"Что хотите сделать с игрой {game.title}?",
        reply_markup=reply_markup,
    )


def show_members(update: Update, context: CallbackContext):
    query = update.callback_query
    game = get_game_by_id(context.user_data["current_game_id"])
    game_members = GameMember.select().where(GameMember.game_id == game.id)

    query.message.reply_text(f"Участники игры {game.title}:")
    available_user_ids = []
    for member in game_members:
        user_form = User.get_by_id(member.user_id)
        query.message.reply_text(
            f"id:{member.id}\n" f"{user_form.name}, email: {user_form.email}"
        )
        available_user_ids.append(member.id)
    context.user_data["available_user_ids"] = available_user_ids
    query.message.reply_text(
        "Чтобы удалить участника введите команду /delete и id участника.\n\n"
        "Например: /delete 15"
    )
    dispatcher.add_handler(
        CommandHandler("delete", call_delete_member, Filters.user(user_ids))
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
                text=f"Пользователя с id {user_id_to_delete} не найдено в этой игре"
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
    query = update.callback_query
    game = get_game_by_id(context.user_data["current_game_id"])
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Провести жеребьевку", callback_data="make_draw")],
        ]
    )
    query.message.reply_text(
        text=f"Провеcти жеребьевку для игры {game.title}",
        reply_markup=reply_markup,
    )


def make_draw(update: Update, context: CallbackContext):
    manual_draw(context.user_data["current_game_id"])


def edit_game(update: Update, context: CallbackContext):
    query = update.callback_query
    game = get_game_by_id(context.user_data["current_game_id"])
    keyboard = [
        [
            InlineKeyboardButton("Название", callback_data="title"),
            InlineKeyboardButton("Стоимость подарка", callback_data="budget"),
        ],
        [
            InlineKeyboardButton("Период регистрации", callback_data="edit_deadline"),
            InlineKeyboardButton("Дату отправки подарка", callback_data="send_date"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
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
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=BUDGET_OPTIONS[0], callback_data=BUDGET_OPTIONS[0]
                    ),
                    InlineKeyboardButton(
                        text=BUDGET_OPTIONS[1], callback_data=BUDGET_OPTIONS[1]
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=BUDGET_OPTIONS[2], callback_data=BUDGET_OPTIONS[2]
                    ),
                    InlineKeyboardButton(
                        text=BUDGET_OPTIONS[3], callback_data=BUDGET_OPTIONS[3]
                    ),
                ],
            ]
        )
        query.edit_message_text(
            text=f"Выберите новый бюджет:", reply_markup=reply_markup
        )

    elif query_value == "edit_deadline":
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        DEADLINE_OPTIONS[0], callback_data=DEADLINE_OPTIONS[0]
                    ),
                    InlineKeyboardButton(
                        DEADLINE_OPTIONS[1], callback_data=DEADLINE_OPTIONS[1]
                    ),
                ],
            ]
        )
        query.edit_message_text(
            text=f"Выберите новый период регистрации:", reply_markup=reply_markup
        )

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
    query = update.callback_query
    query_value = update.callback_query.data

    new_budget = query_value
    game = get_game_by_id(context.user_data["current_game_id"])
    game.budget = new_budget
    game.save()
    query.edit_message_text(text="Ок. Стоимость подарка изменена")


def edit_game_deadline(update: Update, context: CallbackContext):
    query = update.callback_query
    query_value = update.callback_query.data

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


def show_created_games_handler(update: Update, context: CallbackContext):
    user = context.user_data["current_user"]
    keyboard = []
    for game in user.created_games:
        keyboard.append(
            [InlineKeyboardButton(game.title, callback_data=game.game_link_id)]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Игры, в которых вы админ:",
        reply_markup=reply_markup,
    )
    # TODO: Куда-то надо дальше переходить, не понимаю куда


def show_participating_in_games_handler(update: Update, context: CallbackContext):
    user = context.user_data["current_user"]
    member_in_games = Game.select().join(GameMember).where(GameMember.user == user)
    keyboard = []
    for game in member_in_games:
        keyboard.append(
            [InlineKeyboardButton(game.title, callback_data=game.game_link_id)]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Игры, в которых вы участвуете:",
        reply_markup=reply_markup,
    )
    # TODO: Куда-то надо дальше переходить, не понимаю куда


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s", level=logging.INFO
    )

    admins = GameAdmin.select()
    admins_ids = [admin.user_id for admin in admins]
    user_ids = set(admins_ids)

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("games", games, Filters.user(user_ids)))
    dispatcher.add_handler(CallbackQueryHandler(show_game, pattern="^[a-z0-9]{8}$"))
    dispatcher.add_handler(CallbackQueryHandler(show_members, pattern="^members$"))
    dispatcher.add_handler(CallbackQueryHandler(edit_game, pattern="^edit$"))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_draw, pattern="^draw$"))
    dispatcher.add_handler(CallbackQueryHandler(make_draw, pattern="^make_draw$"))
    dispatcher.add_handler(
        CallbackQueryHandler(
            edit_game_deadline,
            pattern=f"^{DEADLINE_OPTIONS[0]}|" f"{DEADLINE_OPTIONS[1]}$",
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            edit_game_budget,
            pattern=f"^{BUDGET_OPTIONS[0]}|{BUDGET_OPTIONS[1]}|"
            f"{BUDGET_OPTIONS[2]}|{BUDGET_OPTIONS[3]}$",
        )
    )

    updater.start_polling()
    updater.idle()
