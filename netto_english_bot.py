from telebot import types
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, desc
from models import *
import random

driver_db = input('Введите драйвер подключения (например: postgresql) : ')
login_db = input('Введите логин : ')
password_db = input('Введите пароль : ')
hostname_db = input('Введите название сервера (например: localhost) : ')
port_db = input('Введите порт сервера (например: 5432) : ')
name_db = input('Введите название базы данных: ')

DSN = f'{driver_db}://{login_db}:{password_db}@{hostname_db}:{port_db}/{name_db}'

engine = sqlalchemy.create_engine(DSN)

Session = sessionmaker(bind=engine)
session = Session()

print("\nBot is running")

create_tables(engine)

tg_token = input('Введите токен бота: ')
bot = telebot.TeleBot(tg_token)

common_words = ['Черный', 'Белый ', 'Красный', 'Голубой', 'Зеленый', 'Ты', 'Мы', 'Наш', 'Он', 'Она']


class Buttons:
    ADD_WORD = types.KeyboardButton('Добавить слово \U00002728')
    DELETE_WORD = types.KeyboardButton('Удалить слово \U0001F6AB')
    NEXT = types.KeyboardButton('Дальше \U000027A1')
    OK_GO = types.KeyboardButton('Окей, поехали!')


select_count = session.query(func.count(Words.id))
count_words = select_count.scalar()
if count_words == 0:
    for word in common_words:
        tr_word = translate_word(word)
        add_word = Words(ru_word=word, translate=tr_word)
        session.add(add_word)
        session.commit()
else:
    pass


def add_new_word(message):
    new_ru_word = message.text
    query_new_user_id = session.query(Users.id).filter(Users.uid == message.from_user.id).all()
    new_user_id = [str(i).strip("(',) ") for i in query_new_user_id]

    check_word_in_vocabulary = (session.query(Vocabulary.id).
                                join(Users, Users.id == Vocabulary.user_id).
                                join(Words, Words.id == Vocabulary.word_id).
                                filter(Users.uid == message.chat.id, Words.ru_word.ilike(new_ru_word))).all()

    check_word_in_words = session.query(Words.ru_word).filter(Words.ru_word.ilike(new_ru_word)).all()

    if len(check_word_in_vocabulary) == 0 and len(check_word_in_words) == 0:
        ru_to_en = translate_word(new_ru_word)
        add_word_to_words = Words(ru_word=new_ru_word, translate=ru_to_en)
        session.add(add_word_to_words)
        session.commit()

        query_new_word = session.query(Words.id).filter(Words.ru_word.ilike(new_ru_word)).all()
        new_word_id = [str(i).strip("(',) ") for i in query_new_word]

        add_all_to_vocabulary = Vocabulary(user_id=int(new_user_id[0]), word_id=int(new_word_id[0]))
        session.add(add_all_to_vocabulary)
        session.commit()

        select_words_count = (session.query(func.count(Vocabulary.word_id)).
                              join(Users, Users.id == Vocabulary.user_id).filter(Users.uid == message.from_user.id))
        count_words_in_vocabulary = select_words_count.scalar()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)

        bot.send_message(message.from_user.id, f'Слово "{new_ru_word}" с переводом "{ru_to_en}" добавлено \U0001F680'
                                               f'\nОбщее количество слов в словаре = {count_words_in_vocabulary}',
                         reply_markup=markup)

    if len(check_word_in_vocabulary) == 0 and len(check_word_in_words) != 0:
        ru_to_en = translate_word(new_ru_word)

        query_new_word = session.query(Words.id).filter(Words.ru_word.ilike(new_ru_word)).all()
        new_word_id = [str(i).strip("(',) ") for i in query_new_word]

        add_all_to_vocabulary = Vocabulary(user_id=int(new_user_id[0]), word_id=int(new_word_id[0]))
        session.add(add_all_to_vocabulary)
        session.commit()

        select_words_count = (session.query(func.count(Vocabulary.word_id)).
                              join(Users, Users.id == Vocabulary.user_id).filter(Users.uid == message.from_user.id))
        count_words_in_vocabulary = select_words_count.scalar()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)

        bot.send_message(message.from_user.id, f'Слово "{new_ru_word}" с переводом "{ru_to_en}" добавлено \U0001F680'
                                               f'\nОбщее количество слов в словаре = {count_words_in_vocabulary}',
                         reply_markup=markup)

    if len(check_word_in_vocabulary) != 0:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)

        bot.send_message(message.from_user.id, f'Слово "{new_ru_word.lower()}" уже есть в словаре.\n'
                                               f'Выбери нужную команду для продолжения \U000023EC', reply_markup=markup)


def delete_word(message):
    word_for_delete = message.text
    word_id_in_vocabulary = (session.query(Vocabulary).
                             join(Users, Users.id == Vocabulary.user_id).
                             join(Words, Words.id == Vocabulary.word_id).
                             filter(Users.uid == message.chat.id, Words.ru_word.ilike(word_for_delete))).first()

    if word_id_in_vocabulary:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)
        session.delete(word_id_in_vocabulary)
        session.commit()
        bot.send_message(message.chat.id, f'Слово "{word_for_delete}" удалено из словаря', reply_markup=markup)

    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)
        bot.send_message(message.chat.id, f'Слово "{word_for_delete}" не найдено в словаре, '
                                          f'попробуйте выбрать другое слово.',
                         reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(Buttons.OK_GO)

    bot.send_message(message.chat.id, f'Добро пожаловать в мир английского языка!\n\nЭтот тренажёр поможет  '
                                      f'запомнить перевод нужных слов. Мы добавили тебе 10 слов для начала тренировки. '
                                      f'\n\nВ дальнейшем ты можешь добавлять или удалять любые слова в свой собственный '
                                      f'словарь.', reply_markup=markup)

    find_user_in_users = session.query(Users.uid).filter(Users.uid == message.chat.id).all()
    count = len(find_user_in_users)
    if count == 0:
        add_user = Users(uid=message.chat.id)
        session.add(add_user)
        session.commit()
    find_user_in_vocabulary = session.query(Vocabulary.user_id).join(Users).filter(Users.uid == message.chat.id).all()
    count = len(find_user_in_vocabulary)
    if count == 0:
        last_user_id = session.query(Users.id).order_by(desc(Users.id)).limit(1).scalar_subquery()
        common_words_indexes = list(range(1, len(common_words) + 1))

        for i in common_words_indexes:
            add_to_vocabulary = Vocabulary(user_id=last_user_id, word_id=i)
            session.add(add_to_vocabulary)
            session.commit()
    else:
        pass


def random_russian_word(user_id):
    select = session.query(Words.ru_word).join(Vocabulary).join(Users).filter(Users.uid == user_id)
    list_words = [str(i).strip("(',) ") for i in select]
    random_word = random.choice(list_words)
    return random_word


def all_random_words(user_id):
    select = session.query(Words.translate).join(Vocabulary).join(Users).filter(Users.uid == user_id)
    list_words = [str(i).strip("(',) ") for i in select]

    random_ru = random_russian_word(user_id)
    random_ru_to_en = translate_word(random_ru)

    if random_ru_to_en in list_words:
        del list_words[list_words.index(random_ru_to_en)]

    random_english_words = set()
    dict_all_words = {}

    while len(random_english_words) != 3:
        random_word = random.choice(list_words)
        random_english_words.add(random_word)

    dict_all_words['ru_word'] = random_ru
    dict_all_words['en_words'] = list(random_english_words)
    return dict_all_words


def true_translate(ru_word):
    select = session.query(Words.translate).filter(Words.ru_word.ilike(ru_word)).all()
    true_word = str(select[0]).strip("(',) ")
    return true_word


@bot.message_handler(func=lambda message: message.text == Buttons.ADD_WORD.text)
def add_word_button(message):
    message = bot.send_message(message.from_user.id, 'Введите новое слово для добавления:')
    bot.register_next_step_handler(message, add_new_word)


@bot.message_handler(func=lambda message: message.text == Buttons.NEXT.text)
def next_word_button(message):
    bot.send_message(message.from_user.id, f'Хорошо, идём дальше')
    ok_go_button(message)


@bot.message_handler(func=lambda message: message.text == Buttons.DELETE_WORD.text)
def delete_word_button(message):
    bot.send_message(message.chat.id, 'Введите слово для удаления: ')
    bot.register_next_step_handler(message, delete_word)


@bot.message_handler(func=lambda message: message.text == Buttons.OK_GO.text)
def ok_go_button(message):
    random_words = all_random_words(message.chat.id)

    ru_word = random_words["ru_word"]
    translate_true_ru_word = translate_word(random_words['ru_word'])
    en_but_1 = random_words['en_words'][0]
    en_but_2 = random_words['en_words'][1]
    en_but_3 = random_words['en_words'][2]
    words = [ru_word, translate_true_ru_word, en_but_1, en_but_2, en_but_3]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    translate_but_true = types.KeyboardButton(translate_true_ru_word)
    translate_but_2 = types.KeyboardButton(en_but_1)
    translate_but_3 = types.KeyboardButton(en_but_2)
    translate_but_4 = types.KeyboardButton(en_but_3)
    words_buttons = [translate_but_true, translate_but_2, translate_but_3, translate_but_4]
    random.shuffle(words_buttons)

    markup.add(*words_buttons, Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)
    msg = bot.send_message(message.chat.id, f'Выберите перевод слова:\n'
                                            f' \U0001F1F7\U0001F1FA {random_words["ru_word"]}', reply_markup=markup)

    def get_button_variable(msg_b):
        if (msg_b.text == translate_true_ru_word or msg_b.text == en_but_1 or
                msg_b.text == en_but_2 or msg_b.text == en_but_3):
            correct_answer(msg_b, *words)
        if msg_b.text == Buttons.ADD_WORD.text:
            add_word_button(msg_b)
        if msg_b.text == Buttons.NEXT.text:
            next_word_button(msg_b)
        if msg_b.text == Buttons.DELETE_WORD.text:
            delete_word_button(msg_b)

    bot.register_next_step_handler(msg, get_button_variable)


def correct_answer(msg, ru_word, translate_true_ru_word, en_but_1, en_but_2, en_but_3):
    words = [ru_word, translate_true_ru_word, en_but_1, en_but_2, en_but_3]
    text = msg.text
    chat_id = msg.from_user.id
    if text == translate_true_ru_word:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        markup.add(Buttons.NEXT, Buttons.ADD_WORD, Buttons.DELETE_WORD)

        bot.send_message(chat_id, f'Правильно \U00002728\n{ru_word}   \U000027A1   {translate_true_ru_word}',
                         reply_markup=markup)

    if text == en_but_1 or text == en_but_2 or text == en_but_3:
        bot.send_message(chat_id, f'Неправильно \U0001F622\nПопробуйте ещё раз')
        bot.register_next_step_handler(msg, correct_answer, *words)

    if text == Buttons.ADD_WORD.text:
        add_word_button(msg)
    if text == Buttons.NEXT.text:
        next_word_button(msg)
    if text == Buttons.DELETE_WORD.text:
        delete_word_button(msg)


bot.infinity_polling()

session.close()
