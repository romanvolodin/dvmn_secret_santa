import random

from models import GameMember, Match, Game


def draw():
    games = Game.select()
    for game in games:
        users = GameMember.select().where(GameMember.game=game.id)

        random.shuffle(users)
        for i in range(len(users)):
            giver = users[i]
            recipient = users[(i+1) % (len(users))]

            Match.create(
                game = game.id,
                giver = giver.id,
                recipient = recipient.id,
            )