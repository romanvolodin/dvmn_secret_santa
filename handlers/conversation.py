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

from handlers import member, admin
from handlers import game as gm
from models import Game, GameMember, GameAdmin, User


def start(update: Update, context: CallbackContext):
    current_user = User.get_or_none(User.id == update.effective_user.id)
    admin_in_games = None
    member_in_games = None
    if current_user:
        context.user_data["current_user"] = current_user
        admin_in_games = (
            Game.select().join(GameAdmin).where(GameAdmin.user == current_user)
        )
        member_in_games = (
            Game.select().join(GameMember).where(GameMember.user == current_user)
        )
        if admin_in_games:
            context.user_data["is_admin"] = True

    if context.args:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]]
        )
        game = Game.get_or_none(Game.game_link_id == context.args[0])
        if not game:
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=gm.create_button_text)]]
            )
            update.message.reply_text(
                text=f"Игра с id '{context.args[0]}' не найдена.\n"
                "Не расстраивайтесь, создайте новую игру.",
                reply_markup=reply_markup,
            )
            return gm.GET_TITLE

        if game:
            context.user_data["current_game"] = game
            if member_in_games is not None and game in member_in_games:
                update.message.reply_text("Вы уже в игре!")
                return member.INITIAL_CHOICE

            reply_markup = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=member.button_accept)],
                    [KeyboardButton(text=member.button_cancel)],
                ]
            )
            update.message.reply_text(
                text=f"Замечательно, ты собираешься участвовать в игре “{game.title}“:\n"
                f"• ограничение стоимости подарка: {game.budget},\n"
                f"• период регистрации: до {game.deadline.strftime('%d.%m.%Y, %H:%M(МСК)')},\n"
                f"• дата отправки подарков: {game.gift_send_date.strftime('%d.%m.%Y')}",
                reply_markup=reply_markup,
            )
            if member_in_games:
                return member.ADD_EXISTED_USER_TO_GAME
            return member.NAME

    if admin_in_games:
        update.message.reply_text(
            f"Вы создали {len(admin_in_games)} игр и участвуете в {len(member_in_games)} играх.",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Посмотреть созданные", "Посмотреть, где участвую"],
                    ["Создать новую игру", "Поменять данные"],
                ],
                resize_keyboard=True,
            ),
        )
        return admin.INITIAL_CHOICE

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
            MessageHandler(Filters.regex("^Создать игру$"), gm.game_title_handler),
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
        admin.INITIAL_CHOICE: [
            MessageHandler(
                Filters.regex("^Посмотреть созданные$"),
                admin.show_created_games_handler,
            ),
            MessageHandler(
                Filters.regex("^Посмотреть, где участвую$"),
                admin.show_participating_in_games_handler,
            ),
            MessageHandler(
                Filters.regex("^Создать новую игру$"),
                gm.game_title_handler,
            ),
            MessageHandler(
                Filters.regex("^Поменять данные$"),
                member.change_data_choice_handler,
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", gm.cancel)],
)
