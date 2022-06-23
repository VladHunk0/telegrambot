from pymongo import MongoClient

class GapsBase:
    def __init__(self):
        cluster = MongoClient("mongodb+srv://userVlad:123@cluster0.zmye5.mongodb.net/?retryWrites=true&w=majority")

        self.dg = cluster["TelegramBot"]
        self.user = self.dg["Users_Gaps"]
        self.questions = self.dg["Gaps"]
        self.questions_count = len(list(self.questions.find({})))
    
    def get_user(self, chat_id):
        user = self.user.find_one({"chat_id": chat_id})

        if user is not None:
            return user

        user = {
            "chat_id": chat_id,
			"is_passing": False,
			"is_passed": False,
			"question_index": None,
			"answers": []
        }

        self.user.insert_one(user)
        return user

    def set_user(self, chat_id, update):
        self.user.update_one({"chat_id": chat_id}, {"$set": update})

    def get_question(self, index): 
        return self.questions.find_one({"id": index})

dg = GapsBase()
