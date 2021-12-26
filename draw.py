import datetime
import random

import telegram

from environs import Env
from models import GameMember, Match, Game, User, GameAdmin


def draw(users, game_id):
    if len(users) < 2:
        return False
    random.shuffle(users)
    for i in range(len(users)):
        giver = users[i]
        recipient = users[(i + 1) % (len(users))]
        Match.create(
            game=game_id,
            giver=giver,
            recipient=recipient,
        )
    return True


def automatic_draw():
    msk_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    games = Game.select()
    for game in games:
        if game.deadline == msk_time:
            users = GameMember.select().where(GameMember.game_id == game.id)
            users_ids = [user.user_id for user in users]
            if draw(users_ids, game.id):
                send_contacts(game.id)
            else:
                send_error_msg(game.id)


def manual_draw(game_link_id):
    game_id = Game.get(Game.game_link_id == game_link_id)
    users = GameMember.select().where(GameMember.game_id == game_id)
    users_ids = [user.user_id for user in users]
    if draw(users_ids, game_id):
        send_contacts(game_id)
    else:
        send_error_msg(game_id)


def send_contacts(game_id):
    all_matches = Match.select().where(Match.game == game_id)
    for match in all_matches:
        giver_id = match.giver_id
        recipient_id = match.recipient_id
        game = Game.get(Game.id == game_id)
        message = create_msg(recipient_id, game)
        bot.sendMessage(chat_id=giver_id, text=message)


def create_msg(recipient_id, game):
    recipient = User.get_by_id(recipient_id)
    text = (
        f"🎉 Жеребьевка в игре “{game.title}” проведена! Спешу сообщить кто тебе выпал:\n"
        f"• Имя получателя: {recipient.name}\n"
        f"• Email: {recipient.email}\n"
        f"• Пожелания: {recipient.wishlist}\n"
        f"• Интересы: {recipient.interests}\n"
        f"• Записка для Санты: {recipient.letter}\n\n"
        f"Условия игры:\n"
        f"Ограничение стоимости подарка: {game.budget}\n"
        f"Подарок нужно отправить {game.gift_send_date.strftime('%d.%m.%Y')}."
    )
    return text


def send_error_msg(game_id):
    game = Game.get(Game.id == game_id)
    admin_id = GameAdmin.get_by_id(game_id).user_id
    draw_error_msg = (
        f"🥺 К сожалению, в игре “{game.title}“ слишком мало "
        f"участников для проведения жеребьевки"
    )
    bot.sendMessage(chat_id=admin_id, text=draw_error_msg)


if __name__ == "__main__":
    env = Env()
    env.read_env()
    bot = telegram.Bot(token=env.str("BOT_TOKEN"))
