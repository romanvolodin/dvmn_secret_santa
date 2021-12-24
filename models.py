from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    TextField,
    DateTimeField,
    ForeignKeyField,
)


db_file = "secret_santa.db"
db = SqliteDatabase(db_file, pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField(default="")
    email = CharField(default="")
    wishlist = TextField(default="")
    interests = TextField(default="")
    letter = TextField(default="")


class Game(BaseModel):
    game_link_id = CharField()
    title = CharField()
    deadline = DateTimeField()
    budget = CharField()
    gift_send_date = DateTimeField()
    created_by = ForeignKeyField(User, backref="games")


class GameAdmin(BaseModel):
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)


class GameMember(BaseModel):
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)


class Match(BaseModel):
    game = ForeignKeyField(Game)
    giver = ForeignKeyField(User)
    recipient = ForeignKeyField(User)
