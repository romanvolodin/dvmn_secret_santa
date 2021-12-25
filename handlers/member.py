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
from models import User, GameMember

NAME, EMAIL, WISHLIST, INTERESTS, LETTER, FINISH = range(5, 11)
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
        f"{game.deadline} мы проведем жеребьевку и ты "
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


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена регистрации")
    return ConversationHandler.END
