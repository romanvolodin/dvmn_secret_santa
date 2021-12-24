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


class User(Model):
    name = CharField(default="")
    email = CharField(default="")
    wishlist = TextField(default="")
    interests = TextField(default="")
    letter = TextField(default="")

    class Meta:
        database = db


class Game(Model):
    reg_link = CharField()
    title = CharField()
    deadline = DateTimeField()
    budget = CharField()
    gift_send_date = DateTimeField()
    created_by = ForeignKeyField(User, backref="games")

    class Meta:
        database = db


class GameAdmin(Model):
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)

    class Meta:
        database = db


class GameMember(Model):
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)

    class Meta:
        database = db


class Match(Model):
    game = ForeignKeyField(Game)
    giver = ForeignKeyField(User)
    recipient = ForeignKeyField(User)

    class Meta:
        database = db
