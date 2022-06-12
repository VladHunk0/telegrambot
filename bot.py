import telebot
import config
from pymongo import MongoClient


bot = telebot.TeleBot(config.TOKEN)

class DataBase:
    def __init__(self):
        cluster = MongoClient("mongodb+srv://userVlad:123@cluster0.zmye5.mongodb.net/?retryWrites=true&w=majority")

        self.db = cluster["TelegramBot"]
        self.users = self.db["Users"]
        self.questions = self.db["Questions"]

        self.questions_count = len(list(self.questions.find({})))
    
    def get_user(self, chat_id):
        user = self.users.find_one({"chat_id": chat_id})

        if user is not None:
            return user

        user = {
            "chat_id": chat_id,
			"is_passing": False,
			"is_passed": False,
			"question_index": None,
			"answers": []
        }

        self.users.insert_one(user)

        return user

    def set_user(self, chat_id, update):
        self.users.update_one({"chat_id": chat_id}, {"$set": update})

    def get_question(self, index): 
        return self.questions.find_one({"id": index})

db = DataBase()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
    "🔥Вітаю тебе, майбутній абітурієнте, <b>{0.first_name}</b>!🔥\n"
    "Я - <b>{1.first_name}</b>, бот, який доможе тобі підготуватись до ЗНО з англійської мови швидко та цікаво.🎓".format(message.from_user, bot.get_me()),
    parse_mode='html')
    bot.send_message(message.chat.id,
    "Для того щоб розпочати тестування пропишіть команду - /test")

@bot.message_handler(commands=['test'])
def test(message):
    user = db.get_user(message.chat.id)

    if user["is_passed"]:
        bot.send_message(message.from_user.id, "Ви уже проходили дане тестування.")
        return

    if user["is_passing"]:
        return

    db.set_user(message.chat.id, {"question_index": 0, "is_passing": True})

    user = db.get_user(message.chat.id)
    post = get_question_message(user)
    if post is not None:
        bot.send_message(message.from_user.id, post["text"], reply_markup=post["keyboard"])

@bot.callback_query_handler(func=lambda query: query.data.startswith("?ans"))
def answered(query):
    user = db.get_user(query.message.chat.id)

    if user["is_passed"] or not user["is_passing"]:
        return
    
    user["answers"].append(int(query.data.split("&")[1]))
    db.set_user(query.message.chat.id, {"answers": user["answers"]})

    post = get_answered_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id,
        reply_markup=post["keyboard"])

@bot.callback_query_handler(func=lambda query: query.data == "?next")
def next(query):
    user = db.get_user(query.message.chat.id)

    if user["is_passed"] or not user["is_passing"]:
        return
    
    user["question_index"] += 1
    db.set_user(query.message.chat.id, {"question_index": user["question_index"]})

    post = get_question_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id,
        reply_markup=post["keyboard"])

def get_question_message(user):
    if user["question_index"] == db.questions_count:
        count = 0
        for question_index, question in enumerate(db.questions.find({})):
            if question["correct"] == user["answers"][question_index]:
                count += 1

        if count < 15:
            smile = "😥"
        elif count < 25:
            smile = "😐"
        elif count < 35:
            smile = "😀"
        else:
            smile = "😎"

        text = f"К-ть правильних відповідей - {count}, {smile}. \nВсього завдань - {db.questions_count}."

        db.set_user(user["chat_id"], {"is_passed": True, "is_passing": False})

        return {
            "text": text,
            "keyboard": None
        }

    question = db.get_question(user["question_index"])

    if question is None:
        return
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    for answer_index, answer in enumerate(question["answers"]):
        keyboard.row(telebot.types.InlineKeyboardButton(f"{chr(answer_index + 97)}) {answer}",
        callback_data=f"?ans&{answer_index}"))
    
    text = f"Питтаня №{user['question_index'] + 1}\n\n{question['text']}"
    return {
        "text": text,
        "keyboard": keyboard
    }

def get_answered_message(user):
    question = db.get_question(user["question_index"])

    text = f"Питання №{user['question_index'] + 1}\n\n{question['text']}\n"

    for answer_index, answer in enumerate(question["answers"]):
        text += f"{chr(answer_index + 97)}) {answer}"

        if answer_index == question["correct"]:
            text += " ✅"
        elif answer_index == user["answers"][-1]:
            text += " ❌"

        text += "\n"

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton("Далі", callback_data="?next"))

    return {
        "text": text,
        "keyboard": keyboard
    }

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id,
    "<b>Якщо тобі потрібна допомога, ось тобі список моїх команд: </b>\n"
    "/test - Почати тестування\n"
    "/list - Список корисного матеріалу для підготовки до іспиту\n"
    "/help - Допомога з ботом\n"
    "/nuwm - Інформація про університет НУВГП\n"
    "/contact - Показати контактну інформацію".format(message.from_user, bot.get_me()),
    parse_mode='html')

@bot.message_handler(commands=['list'])
def list(message):
    bot.send_message(message.chat.id,
    "<b>Я підібрав для тебе список корисних джерел, які покращать твою підготовку до ЗНО:</b>\n\n"
    "1️⃣ Ні для кого не секрет, що аудіювання є одною із найскладніших тем, які подані на ЗНО. Тому спеціально для тебе я підібрав ось такий <a href='https://www.listeninenglish.com/'>сайт</a>. Гадаю, він зможе покращити твій рівень розуміння аудіювання.\n\n"
    "2️⃣ <a href='https://puzzle-english.com/level-test'>Puzzle English</a> – онлайн-платформа для самостійного вивчення англійської мови. Розвиває практику розуміння на слух, читання, письма та мовлення.\n\n"
    "3️⃣ <a href='https://www.cambridgeenglish.org/test-your-english/'>CELA</a>, Кембриджські іспити - група іспитів з англійської мови, що проводяться однойменним підрозділом екзаменаційної ради Кембриджського університету.\n\n"
    "4️⃣ Ще одним з нелегких завдань є завдання типу USE of ENGLISH. Тому ось тобі <a href='https://youtu.be/V4g--Khx-ME'>порада</a>, як правильно його виконувати.\n\n"
    "5️⃣ 100 англійських <a href='https://cambridge.ua/blog/100-phrasal-verbs-you-need-to-know/'>фразових дієслів</a>, які має знати кожен.\n\n"
    "6️⃣ ТОП-30 <a href='https://enguide.ua/magazine/30-idiom-na-angliyskom-i-kak-ih-pravilno-ispolzovat'>ідіом</a> в англійській мові.\n\n"
    "7️⃣ Ну і наостанок, ось тобі <a href='https://zno.osvita.ua/english/'>сторінка</a>, звідки я даю змогу тобі пройти тести.".format(message.from_user, bot.get_me()),
    parse_mode='html')

@bot.message_handler(commands=['nuwm'])
def nuwm(message):
    bot.send_message(message.chat.id,
    "<b>Що за університет НУВГП ? 🤔</b>\n\n"
    "Окей, спробую розповісти. <b>НУВГП</b> - це не просто університет. Запитаєш чому ? Думаю я зможу відповісти на твоє питання.\n\n"
    "Ставши нашим студентом, ти отримаєш власну корпоративну пошту, яка дасть тобі можливість користуватися сервісами Google. Крім цього - у подарунок безлімітний Google Drive, який залишиться з тобою і після завершення навчання. Також ти матимеш персональний кабінет у навчальній платформі Moodle, персональний мобільний додаток 'Мій НУВГП', сервіс онлайн-підтримки HelpDesk та електронний деканат, а також доступ до платформи міжнародних курсів для саморозвитку та вдосконалення Coursera.\n\n"
    "До складу університету входить 9 навчально-наукових інститутів: водного господарства та природооблаштування; механічний; агроекології та землеустрою; будівництва та архітектури; автоматики, кібернетики та обчислювальної техніки; економіки та менеджменту; права; охорони здоров`я, заочно-дистанційного навчання, а також Інститут післядипломної освіти, Надслучанський інститут, 5 коледжів, 5 локальних центрів дистанційно-заочного навчання.\n\n"
    "Навчання студентів проводиться в 15 навчальних корпусах, де функціонує понад 100 спеціалізованих аудиторій, кабінетів, оснащених сучасною аудіовізуальною апаратурою, комп’ютерною технікою та іншим обладнанням. В університеті створено унікальні лабораторії гідравліки, гідротехніки, меліорації і ґрунтознавства, установки водоподачі, водопідготовки та водоочистки тощо.\n\n"
    "Якщо я зміг тебе зацікавити, то рекомендую тиснути <a href='https://nuwm.edu.ua/'>сюди</a>.".format(message.from_user, bot.get_me()),
    parse_mode='html')

@bot.message_handler(commands=['contact'])
def contact(message):
    bot.send_message(message.chat.id,
    "Пишіть @vlad_hunko або телефонуйте за номером:\n"
    "+38 (097) 32-35-357\n")
    bot.send_message(message.chat.id,
    "Також можете писати на електронну адресу:\n"
    "vlad.hunko10a@gmail.com\n")

bot.polling(none_stop=True)