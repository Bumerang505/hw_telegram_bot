import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship
import translators as ts
import telebot

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = sq.Column(sq.Integer, primary_key=True)
    uid = sq.Column(sq.BigInteger, unique=True, nullable=False)

    def __str__(self):
        return f'[{self.id}, {self.uid}]'


class Words(Base):
    __tablename__ = "words"

    id = sq.Column(sq.Integer, primary_key=True)
    ru_word = sq.Column(sq.String(length=80),unique=True, nullable=False)
    translate = sq.Column(sq.String(length=80), nullable=False)

    def __str__(self):
        return f'[{self.id}, {self.ru_word}, {self.translate}]'


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey(Users.id), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey(Words.id), nullable=False)

    def __str__(self):
        return f'[{self.id}, {self.user_id}, {self.word_id}]'

    vocabulary_1 = relationship(Users, backref='vocabulary')
    vocabulary_2 = relationship(Words, backref='vocabulary')


def create_tables(engine):
    Base.metadata.create_all(engine)


def remove_tables(engine):
    Base.metadata.drop_all(engine)


def translate_word(word):
    q_text = word
    return ts.translate_text(q_text, translator='google')
