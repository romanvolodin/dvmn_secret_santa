from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

from handlers import member
from handlers import game as gm
from models import Game, GameMember


def start(update: Update, context: CallbackContext):
    member_in_db = (
        GameMember.select()
        .where(GameMember.user_id == update.message.from_user.id)
        .get_or_none()
    )  # Кто-нибудь! Уберите этот ужас...
    if context.args:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]]
        )
        game = Game.get_or_none(Game.game_link_id == context.args[0])
        if not game:
            update.message.reply_text(
                f"Игра с id '{context.args[0]}' не найдена.\n"
                "Не расстраивайтесь, создайте новую игру."
            )
        if game:
            if member_in_db:
                member_in_game = (
                    GameMember.select()
                    .where(GameMember.game_id == game.id)
                    .get_or_none()
                )
                if member_in_game:
                    update.message.reply_text(
                        "Вы уже в игре!\n",
                        reply_markup=ReplyKeyboardMarkup(
                            [
                                ["Посмотреть игры", "Создать игру"],
                                ["Поменять регистрационные данные"],
                            ],
                            resize_keyboard=True,
                        ),
                    )
                    return member.INITIAL_CHOICE
                else:
                    reply_markup = ReplyKeyboardMarkup(
                        keyboard=[
                            [KeyboardButton(text=member.button_accept)],
                            [KeyboardButton(text=member.button_cancel)],
                        ]
                    )
                    context.user_data["current_game"] = game
                    update.message.reply_text(
                        text=f"Замечательно, ты собираешься участвовать в игре “{game.title}“:\n"
                        f"• ограничение стоимости подарка: {game.budget},\n"
                        f"• период регистрации: до {game.deadline.strftime('%d.%m.%Y, %H:%M(МСК)')},\n"
                        f"• дата отправки подарков: {game.gift_send_date.strftime('%d.%m.%Y')}",
                        reply_markup=reply_markup,
                    )
                    return member.ADD_EXISTED_USER_TO_GAME
            else:
                reply_markup = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=member.button_accept)],
                        [KeyboardButton(text=member.button_cancel)],
                    ]
                )
                context.user_data["current_game"] = game
                update.message.reply_text(
                    text=f"Замечательно, ты собираешься участвовать в игре “{game.title}“:\n"
                    f"• ограничение стоимости подарка: {game.budget},\n"
                    f"• период регистрации: до {game.deadline.strftime('%d.%m.%Y, %H:%M(МСК)')},\n"
                    f"• дата отправки подарков: {game.gift_send_date.strftime('%d.%m.%Y')}",
                    reply_markup=reply_markup,
                )
                return member.NAME
    elif member_in_db:
        update.message.reply_text(
            "Вы участвуете в N играх",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Посмотреть игры", "Создать игру"],
                    ["Поменять регистрационные данные"],
                ],
                resize_keyboard=True,
            ),
        )
        return member.INITIAL_CHOICE

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=gm.create_button_text)]]
    )
    update.message.reply_text(
        text="Организуй тайный обмен подарками, запусти праздничное настроение!",
        reply_markup=reply_markup,
    )
    return gm.GET_TITLE


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        gm.GET_TITLE: [
            MessageHandler(
                Filters.regex(gm.create_button_text),
                gm.game_title_handler,
                pass_user_data=True,
            )
        ],
        gm.GET_BUDGET: [
            MessageHandler(
                Filters.text ^ Filters.command,
                gm.budget_handler,
                pass_user_data=True,
            )
        ],
        gm.GET_DEADLINE: [
            MessageHandler(
                Filters.regex(
                    f"^({gm.BUDGET_OPTIONS[0]}|"
                    f"{gm.BUDGET_OPTIONS[1]}|"
                    f"{gm.BUDGET_OPTIONS[2]}|"
                    f"{gm.BUDGET_OPTIONS[3]})$"
                ),
                gm.deadline_handler,
                pass_user_data=True,
            )
        ],
        gm.GET_SEND_DATE: [
            MessageHandler(
                Filters.regex(
                    f"^({gm.DEADLINE_OPTIONS[0]}|" f"{gm.DEADLINE_OPTIONS[1]})$"
                ),
                gm.send_date_handler,
                pass_user_data=True,
            )
        ],
        gm.GET_FINISH: [
            MessageHandler(
                Filters.regex(gm.regex_for_date) | Filters.command,
                gm.finish_handler,
                pass_user_data=True,
            )
        ],
        member.NAME: [
            MessageHandler(
                Filters.regex(f"^({member.button_accept}|{member.button_cancel})$"),
                member.username_handler,
                pass_user_data=True,
            )
        ],
        member.EMAIL: [
            MessageHandler(
                Filters.text ^ Filters.command,
                member.email_handler,
                pass_user_data=True,
            )
        ],
        member.WISHLIST: [
            MessageHandler(
                Filters.regex(member.regex_for_email) ^ Filters.command,
                member.wishlist_handler,
                pass_user_data=True,
            )
        ],
        member.INTERESTS: [
            MessageHandler(
                Filters.text ^ Filters.command,
                member.interests_handler,
                pass_user_data=True,
            )
        ],
        member.LETTER: [
            MessageHandler(
                Filters.text ^ Filters.command,
                member.letter_handler,
                pass_user_data=True,
            )
        ],
        member.FINISH: [
            MessageHandler(
                Filters.text ^ Filters.command,
                member.finish_handler,
                pass_user_data=True,
            )
        ],
        member.INITIAL_CHOICE: [
            MessageHandler(
                Filters.regex("^Посмотреть игры$"), member.show_games_handler
            ),
            MessageHandler(Filters.regex("^Создать игру$"), member.create_game_handler),
            MessageHandler(
                Filters.regex("^Поменять регистрационные данные$"),
                member.change_data_choice_handler,
            ),
        ],
        member.CHANGE_DATA_CHOICE: [
            MessageHandler(
                Filters.regex("^Имя$|^email$|^Пожелания$|^Интересы$|^Письмо Санте$"),
                member.change_data_handler,
            ),
            MessageHandler(Filters.regex("^Ничего$"), member.change_nothing_handler),
        ],
        member.GET_NEW_DATA: [
            MessageHandler(Filters.text, member.get_new_data_handler),
        ],
        member.ADD_EXISTED_USER_TO_GAME: [
            MessageHandler(
                Filters.regex(f"^({member.button_accept}|{member.button_cancel})$"),
                member.add_user_to_game_handler,
                pass_user_data=True,
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", gm.cancel)],
)
