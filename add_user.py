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
    update.message.reply_text(text="Представьтесь:",
                              reply_markup=ReplyKeyboardRemove())
    return EMAIL


def email_handler(update: Update, context: CallbackContext):
    context.user_data["name"] = update.message.text
    print("Имя пользователя:", context.user_data["name"])

    update.message.reply_text("Ваш mail:")
    return WISHLIST


def wishlist_handler(update: Update, context: CallbackContext):
    context.user_data["email"] = update.message.text
    print("Email:", context.user_data["email"])

    update.message.reply_text("Пожелания:")
    return INTERESTS


def interests_handler(update: Update, context: CallbackContext):
    context.user_data["wishlist"] = update.message.text
    print("Wishlist:", context.user_data["wishlist"])

    update.message.reply_text("Ваши интересы:")
    return LETTER


def letter_handler(update: Update, context: CallbackContext):
    context.user_data["interests"] = update.message.text
    print("Интересы:", context.user_data["interests"])

    update.message.reply_text("Можете написать письмо Санте:")
    return FINISH


def finish_handler(update: Update, context: CallbackContext):
    context.user_data["letter"] = update.message.text
    print("Текст письма", context.user_data["letter"])
    update.message.reply_text(
        "Превосходно, ты в игре! {deadline} мы проведем жеребьевку и ты "
        "узнаешь имя и контакты своего тайного друга. "
        "Ему и нужно будет подарить подарок!"
    )
    print(context.user_data)  # словарь с введенными данными
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена регистрации")
    return ConversationHandler.END


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logging.basicConfig(
        format="%(levelname)s: %(asctime)s - %(name)s - %(message)s",
        level=logging.INFO
    )

    NAME, EMAIL, WISHLIST, INTERESTS, LETTER, FINISH = range(6)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [
                MessageHandler(
                    Filters.regex(f"^({button_accept}|{button_cancel})$"),
                    username_handler,
                    pass_user_data=True,
                )
            ],
            EMAIL: [
                MessageHandler(
                    Filters.text ^ Filters.command,
                    email_handler,
                    pass_user_data=True
                )
            ],
            WISHLIST: [
                MessageHandler(
                    Filters.regex(regex_for_email) ^ Filters.command,
                    wishlist_handler,
                    pass_user_data=True,
                )
            ],
            INTERESTS: [
                MessageHandler(
                    Filters.text ^ Filters.command,
                    interests_handler,
                    pass_user_data=True,
                )
            ],
            LETTER: [
                MessageHandler(
                    Filters.text ^ Filters.command,
                    letter_handler,
                    pass_user_data=True
                )
            ],
            FINISH: [
                MessageHandler(
                    Filters.text ^ Filters.command,
                    finish_handler,
                    pass_user_data=True
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    updater = Updater(token=env.str("BOT_TOKEN"), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
