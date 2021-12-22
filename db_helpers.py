from models import (
    db,
    User,
    Game,
    GameAdmin,
    GameMember,
    Match,
)


def create_db():
    db.connect()
    db.create_tables([User, Game, GameAdmin, GameMember, Match])
