import random

from models import GameMember, Match, Game


def draw(users):
    random.shuffle(users)
    for i in range(len(users)):
        giver = users[i]
        recipient = users[(i + 1) % (len(users))]
        Match.create(
            game=game.id,
            giver=giver.id,
            recipient=recipient.id,
        )


def automatic_draw():
    games = Game.select()
    for game in games:
        users = GameMember.select().where(GameMember.game == game.id)
        draw(users)


def manual_draw(game_id):
    users = GameMember.select().where(GameMember.game == game_id)
    draw(users)
