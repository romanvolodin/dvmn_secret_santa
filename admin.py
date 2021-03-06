import datetime as dt
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils import helpers

from draw import make_draw as _make_draw
from handlers.game import BUDGET_OPTIONS, DEADLINE_OPTIONS, regex_for_date
from models import Game, GameAdmin, GameMember, User


INITIAL_CHOICE = range(1)
button_cancel = "Отмена"


def games(update: Update, context: CallbackContext):
    effective_user_id = update.effective_user.id
    admins_games = Game.select().where(Game.created_by == effective_user_id)
    games_id_titles = [(game.game_link_id, game.title) for game in admins_games]

    keyboard = []
    for game_id, game_title in games_id_titles:
        keyboard.append([InlineKeyboardButton(game_title, callback_data=game_id)])

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
            InlineKeyboardButton(
                "Ссылка для регистрации в игре", callback_data="show_link"
            ),
        ],
        [
            InlineKeyboardButton("Провести жеребьевку", callback_data="draw"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        text=f"Что хотите сделать с игрой “{game.title}“?",
        reply_markup=reply_markup,
    )


def show_link(update: Update, context: CallbackContext):
    current_game_id = context.user_data["current_game_id"]
    bot_username = context.bot.username
    deep_link = helpers.create_deep_linked_url(bot_username, current_game_id)
    update.callback_query.message.reply_text(
        f"Ссылка для регистрации в игре: {deep_link}"
    )


def show_members(update: Update, context: CallbackContext):
    query = update.callback_query
    game = get_game_by_id(context.user_data["current_game_id"])
    game_members = GameMember.select().where(GameMember.game_id == game.id)

    available_user_ids, keyboard = [], []
    for member in game_members:
        user_form = User.get_by_id(member.user_id)
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{user_form.name}, email: {user_form.email}",
                    callback_data=member.id,
                )
            ]
        )
        available_user_ids.append(member.id)

    context.user_data["available_user_ids"] = available_user_ids
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        text=f"Участники игры “{game.title}“.\n\n"
        f"Выберите участника, чтобы удалить или назначить админом",
        reply_markup=reply_markup,
    )


def call_delete_member(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.data
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Да", callback_data=f"delete_member:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "Назначить админом",
                    callback_data=f"make_admin:{user_id}"
                )
            ],
        ]
    )
    query.message.reply_text(
        text="Что сделать с этим пользователем?",
        reply_markup=reply_markup,
    )


def delete_member(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id_to_delete = int(query.data.split(":")[-1])
    GameMember.delete_by_id(user_id_to_delete)
    query.edit_message_text(text="Ок. Пользователь удален из игры")


def make_admin(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id_to_make_admin = int(query.data.split(":")[-1])
    user_id = GameMember.get(GameMember.id == user_id_to_make_admin).user_id

    game_link_id = context.user_data["current_game_id"]
    game_id = Game.get(Game.game_link_id == game_link_id)
    GameAdmin.create(
            user_id=user_id,
            game_id=game_id,
        )
    query.edit_message_text(text="Ок. Пользователь добавлен в админы игры")


def ask_for_draw(update: Update, context: CallbackContext):
    query = update.callback_query
    game = get_game_by_id(context.user_data["current_game_id"])
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Да", callback_data="make_draw")],
        ]
    )
    query.message.reply_text(
        text=f"Провеcти жеребьевку для игры “{game.title}“ сейчас?",
        reply_markup=reply_markup,
    )


def make_draw(update: Update, context: CallbackContext):
    _make_draw(context.user_data["current_game_id"], bot_token)


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
        text=f"Изменить игру “{game.title}“:\n\n"
        f"Ограничение стоимости подарка: {game.budget}\n"
        f"Регистрация до: {game.deadline.strftime('%d.%m.%Y, %H:%M(МСК)')}\n"
        f"Дата отправки подарков: {game.gift_send_date.strftime('%d.%m.%Y')}\n\n"
        f"Что изменить?",
        reply_markup=reply_markup,
    )
    admin_updater.dispatcher.add_handler(CallbackQueryHandler(handle_game_edit))


def handle_game_edit(update: Update, context: CallbackContext):
    query = update.callback_query
    query_value = update.callback_query.data
    query.answer()
    if query_value == "title":
        query.edit_message_text(text="Укажите новое название:")
        admin_updater.dispatcher.add_handler(
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
            text="Выберите новый бюджет:", reply_markup=reply_markup
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
            text="Выберите новый период регистрации:", reply_markup=reply_markup
        )

    elif query_value == "send_date":
        query.edit_message_text(
            text="Укажите новую дату отправки подарка в формате 13.01.2022:"
        )
        admin_updater.dispatcher.add_handler(
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


def admin_main(token, updater, dispatcher):
    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s", level=logging.INFO
    )

    admins = GameAdmin.select()
    admins_ids = [admin.user_id for admin in admins]
    user_ids = set(admins_ids)

    global bot_token
    global admin_updater
    bot_token = token
    admin_updater = updater

    dispatcher.add_handler(CommandHandler("games", games, Filters.user(user_ids)))
    dispatcher.add_handler(CallbackQueryHandler(show_game, pattern="^[a-z0-9]{8}$"))
    dispatcher.add_handler(CallbackQueryHandler(show_members, pattern="^members$"))
    dispatcher.add_handler(CallbackQueryHandler(show_link, pattern="^show_link$"))
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
    dispatcher.add_handler(
        CallbackQueryHandler(call_delete_member, pattern="^[0-9]{1,2}$")
    )
    dispatcher.add_handler(
        CallbackQueryHandler(delete_member, pattern="^delete_member\W")
    )
    dispatcher.add_handler(
        CallbackQueryHandler(make_admin, pattern="^make_admin\W")
    )
