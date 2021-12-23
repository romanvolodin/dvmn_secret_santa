import random
from models import GameMember, Match, Game


games = Game.select()
for game in games:
    users = GameMember.select().where(GameMember.game=game.id)

    random.shuffle(users)
    for i in range(len(users)):
        giver = users[i]
        recipient = users[(i+1) % (len(users))]

        print(f"{giver} дарит {recipient}")

        Match.create(
            game = game.id,
            giver = giver.id,
            recipient = giver.id,
        )