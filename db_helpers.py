from datetime import datetime
from pathlib import Path

from peewee import DoesNotExist, fn
from pytz import timezone
from tzlocal import get_localzone

from models import (
    db,
    db_file,
    User,
    Game,
    GameAdmin,
    GameMember,
    Match,
)


def create_db():
    db.connect()
    db.create_tables([User, Game, GameAdmin, GameMember, Match])


def add_game(context_data):
    if not Path(db_file).is_file():
        create_db()

    max_game_id = Game.select(fn.MAX(Game.id)).scalar()
    if max_game_id:
        game_id = max_game_id + 1
    else:
        game_id = 1

    max_admin_id = GameAdmin.select(fn.MAX(GameAdmin.id)).scalar()
    if max_admin_id:
        admin_id = max_admin_id + 1
    else:
        admin_id = 1

    reg_link = "Temporaly empty"  # Тут будет каким-то образом формироваться "ссылка"

    try:
        User.get(User.id == context_data["user_id"])
    except DoesNotExist:
        User.create(id=context_data["user_id"])

    Game.create(
        id=game_id,
        reg_link=reg_link,
        title=context_data["game_title"],
        deadline=context_data["deadline"],
        budget=context_data["budget"],
        gift_send_date=context_data["send_date"],
        created_by=context_data["user_id"],
    )

    GameAdmin.create(id=admin_id, user=context_data["user_id"], game=game_id)


def add_user(context_data):
    max_member_id = GameMember.select(fn.MAX(GameMember.id)).scalar()
    if max_member_id:
        member_id = max_member_id + 1
    else:
        member_id = 1

    try:
        user = User.get(User.id == context_data["user_id"])
        user.name = context_data["name"]
        user.email = context_data["email"]
        user.wishlist = context_data["wishlist"].replace("Пропустить", "")
        user.interests = context_data["interests"].replace("Пропустить", "")
        user.letter = context_data["letter"].replace("Пропустить", "")
        user.save()
    except DoesNotExist:
        User.create(
            id=context_data["user_id"],
            name=context_data["name"],
            email=context_data["email"],
            wishlist=context_data["wishlist"].replace("Пропустить", ""),
            interests=context_data["interests"].replace("Пропустить", ""),
            letter=context_data["letter"].replace("Пропустить", ""),
        )

    GameMember.create(
        id=member_id,
        user=context_data["user_id"],
        game=context_data["game_id"],
    )


if __name__ == "__main__":
    create_db()
