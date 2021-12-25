import datetime
import random

import telegram

from environs import Env
from models import GameMember, Match, Game, User


def draw(users, game_id):
    random.shuffle(users)
    for i in range(len(users)):
        giver = users[i]
        recipient = users[(i + 1) % (len(users))]
        Match.create(
            game=game_id,
            giver=giver,
            recipient=recipient,
        )


def automatic_draw():
    msk_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    games = Game.select()
    for game in games:
        if game.deadline == msk_time:
            users = GameMember.select().where(GameMember.game_id == game.id)
            users_ids = [user.user_id for user in users]
            draw(users_ids, game.id)
            send_contacts(game.id)


def manual_draw(game_link_id):
    game_id = Game.get(Game.game_link_id == game_link_id)
    users = GameMember.select().where(GameMember.game_id == game_id)
    users_ids = [user.user_id for user in users]
    draw(users_ids, game_id)
    send_contacts(game_id)


def send_contacts(game_id):
    all_matches = Match.select().where(Match.game == game_id)
    for match in all_matches:
        giver_id = match.giver_id
        recipient_id = match.recipient_id
        game_title = Game.get(Game.id == game_id).title
        message = create_msg(recipient_id, game_title)
        bot.sendMessage(chat_id=giver_id, text=message)


def create_msg(recipient_id, game_title):
    recipient = User.get_by_id(recipient_id)
    text = (
        f"Жеребьевка в игре “{game_title}” проведена! Спешу сообщить кто тебе выпал:\n"
        f"• Имя получателя: {recipient.name}\n"
        f"• Email: {recipient.email}\n"
        f"• Пожелания: {recipient.wishlist}\n"
        f"• Интересы: {recipient.interests}\n"
        f"• Записка для Санты: {recipient.letter}"
    )
    return text


if __name__ == "__main__":
    env = Env()
    env.read_env()
    bot = telegram.Bot(token=env.str("BOT_TOKEN"))