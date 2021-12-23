from peewee import (
    SqliteDatabase,
    Model,
    IntegerField,
    CharField,
    TextField,
    DateTimeField,
    ForeignKeyField,
)


db_file = "secret_santa.db"
db = SqliteDatabase(db_file)


class User(Model):
    id = IntegerField(unique=True)
    name = CharField(default="")
    email = CharField(default="")
    wishlist = TextField(default="")
    interests = TextField(default="")
    letter = TextField(default="")

    class Meta:
        database = db


class Game(Model):
    id = IntegerField(unique=True)
    reg_link = CharField()
    title = CharField()
    deadline = DateTimeField()
    budget = CharField()
    gift_send_date = CharField()
    created_by = ForeignKeyField(User, backref="games")

    class Meta:
        database = db


class GameAdmin(Model):
    id = IntegerField(unique=True)
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)

    class Meta:
        database = db


class GameMember(Model):
    id = IntegerField(unique=True)
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)

    class Meta:
        database = db


class Match(Model):
    id = IntegerField(unique=True)
    game = ForeignKeyField(Game)
    giver = ForeignKeyField(User)
    recipient = ForeignKeyField(User)

    class Meta:
        database = db
