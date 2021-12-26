import re
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
from handlers import game as gm
from handlers import admin
from models import User, GameMember


NAME, EMAIL, WISHLIST, INTERESTS, LETTER, FINISH = range(5, 11)
INITIAL_CHOICE, CHANGE_DATA_CHOICE, GET_NEW_DATA, ADD_EXISTED_USER_TO_GAME = range(
    12, 16
)
button_accept = "Участвовать"
button_cancel = "Отмена"
regex_for_email = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"


def start(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_accept)],
            [KeyboardButton(text=button_cancel)],
        ]
    )
    update.message.reply_text(
        text="Замечательно, ты собираешься участвовать в игре {game_title},\n"
        "ограничение стоимости подарка: {budget},\n"
        "период регистрации: {deadline},\n"
        "дата отправки подарков: {send_date}",
        reply_markup=reply_markup,
    )
    return NAME


def username_handler(update: Update, context: CallbackContext):
    if update.message.text == button_cancel:
        update.message.reply_text(
            text="Регистрация отменена. Для возобновления введите /start",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    update.message.reply_text(text="Представьтесь:", reply_markup=ReplyKeyboardRemove())
    return EMAIL


def email_handler(update: Update, context: CallbackContext):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Ваш mail:")
    return WISHLIST


def wishlist_handler(update: Update, context: CallbackContext):
    context.user_data["email"] = update.message.text
    update.message.reply_text("Пожелания:")
    return INTERESTS


def interests_handler(update: Update, context: CallbackContext):
    context.user_data["wishlist"] = update.message.text
    update.message.reply_text("Ваши интересы:")
    return LETTER


def letter_handler(update: Update, context: CallbackContext):
    context.user_data["interests"] = update.message.text
    update.message.reply_text("Можете написать письмо Санте:")
    return FINISH


def finish_handler(update: Update, context: CallbackContext):
    context.user_data["letter"] = update.message.text
    game = context.user_data["current_game"]
    update.message.reply_text(
        "Превосходно, ты в игре!\n"
        f"{game.deadline.strftime('%d.%m.%Y в %H:%M(МСК)')} мы проведем жеребьевку и ты "
        "узнаешь имя и контакты своего тайного друга. "
        "Ему и нужно будет подарить подарок!"
    )
    user, is_created = User.get_or_create(
        id=update.message.from_user.id,
        defaults={
            "name": context.user_data["name"],
            "email": context.user_data["email"],
            "wishlist": context.user_data["wishlist"],
            "interests": context.user_data["interests"],
            "letter": context.user_data["letter"],
        },
    )
    if not is_created:
        user.name = context.user_data["name"]
        user.email = context.user_data["email"]
        user.wishlist = context.user_data["wishlist"]
        user.interests = context.user_data["interests"]
        user.letter = context.user_data["letter"]
        user.save()

    GameMember.create(
        user=user,
        game=game,
    )

    return ConversationHandler.END


def show_games_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Не знаю как показать игры (\n" "Верните мне bare SQL syntax!",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Посмотреть игры", "Создать игру"],
                ["Поменять регистрационные данные"],
            ],
            resize_keyboard=True,
        ),
    )
    return INITIAL_CHOICE


def create_game_handler(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=gm.create_button_text)]]
    )
    update.message.reply_text(
        text="Организуй тайный обмен подарками, запусти праздничное настроение!",
        reply_markup=reply_markup,
    )
    return gm.GET_TITLE


def change_data_choice_handler(update: Update, context: CallbackContext):
    context.user_data["data_to_change"] = None
    user = (
        GameMember.select()
        .where(GameMember.user_id == update.message.from_user.id)
        .get()
        .user
    )
    update.message.reply_text(
        f"Ваши регистрационные данные:\n"
        f"• имя: {user.name},\n"
        f"• email: {user.email},\n"
        f"• пожелания: {user.wishlist},\n"
        f"• интересы: {user.interests},\n"
        f"• письмо Санте: {user.letter}\n\n"
        "Что поменять?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Имя", "email", "Пожелания"],
                ["Интересы", "Письмо Санте", "Ничего"],
            ],
            resize_keyboard=True,
        ),
    )
    return CHANGE_DATA_CHOICE


def change_data_handler(update: Update, context: CallbackContext):
    context.user_data["data_to_change"] = update.message.text
    data_to_change = update.message.text.lower()
    update.message.reply_text(
        f"Введите {data_to_change}", reply_markup=ReplyKeyboardRemove()
    )
    return GET_NEW_DATA


def change_nothing_handler(update: Update, context: CallbackContext):
    if context.user_data["data_to_change"]:
        reply = "Изменения сохранены (возможно)"
    else:
        reply = "Что вы хотите?"
    if context.user_data["is_admin"]:
        update.message.reply_text(
            reply,
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Посмотреть созданные", "Посмотреть, где участвую"],
                    ["Создать новую игру", "Поменять данные"],
                ],
                resize_keyboard=True,
            ),
        )
        return admin.INITIAL_CHOICE        
    else:
        update.message.reply_text(
            reply,
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Посмотреть игры", "Создать игру"],
                    ["Поменять регистрационные данные"],
                ],
                resize_keyboard=True,
            ),
        )
        return INITIAL_CHOICE


def get_new_data_handler(update: Update, context: CallbackContext):
    user = (
        GameMember.select()
        .where(GameMember.user_id == update.message.from_user.id)
        .get()
        .user
    )
    user_input = update.message.text
    data_to_change = context.user_data["data_to_change"]
    if data_to_change == "email" and (not re.match(regex_for_email, user_input)):
        update.message.reply_text(
            "Введите корректный email", reply_markup=ReplyKeyboardRemove()
        )
        return GET_NEW_DATA
    elif data_to_change == "Имя":
        user.name = user_input
        user.save()
    elif data_to_change == "email":
        user.email = user_input
        user.save()
    elif data_to_change == "Пожелания":
        user.wishlist = user_input
        user.save()
    elif data_to_change == "Интересы":
        user.interests = user_input
        user.save()
    elif data_to_change == "Письмо Санте":
        user.letter = user_input
        user.save()
    update.message.reply_text(
        "Что ещё поменять?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Имя", "email", "Пожелания"],
                ["Интересы", "Письмо Санте", "Ничего"],
            ],
            resize_keyboard=True,
        ),
    )
    return CHANGE_DATA_CHOICE


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена регистрации")
    return ConversationHandler.END


def add_user_to_game_handler(update: Update, context: CallbackContext):
    if update.message.text == button_cancel:
        update.message.reply_text(
            text="Регистрация отменена. Для возобновления введите /start",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    game = context.user_data["current_game"]
    update.message.reply_text(
        "Превосходно, ты в игре!\n"
        f"{game.deadline.strftime('%d.%m.%Y в %H:%M(МСК)')} мы проведем жеребьевку и ты "
        "узнаешь имя и контакты своего тайного друга. "
        "Ему и нужно будет подарить подарок!",
        reply_markup=ReplyKeyboardRemove(),
    )
    user = User.get(User.id == update.message.from_user.id)
    GameMember.create(
        user=user,
        game=game,
    )

    return ConversationHandler.END
