from datetime import date, datetime
from pathlib import Path

from peewee import fn

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
    
    reg_link = 'Temporaly empty' # Тут будет каким-то образом формироваться "ссылка"

    deadline_str = context_data['deadline']
    deadline = datetime.strptime(f'{deadline_str}', '%d.%m.%Y').date()

    gift_send_date_str = context_data['gift_send_date']
    gift_send_date = datetime.strptime(f'{gift_send_date_str}', '%d.%m.%Y').date()

    try:
        User.get(User.id == context_data['user_id'])
    except:
        User.create(
            id=context_data['user_id']         
        )

    Game.create(
        id=game_id,
        reg_link=reg_link,
        title=context_data['game_name'],
        deadline=deadline,
        budget=context_data['cost'],
        gift_send_date=gift_send_date,
        created_by=context_data['user_id']
    )

    GameAdmin.create(
        id=admin_id,
        user=context_data['user_id'],
        game=game_id
    )
