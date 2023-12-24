from typing import Dict, Any


class User:
    """
    Класс User, описывает критерии поиска по id пользователя
    Args:
        user_id(int): передается id пользователя
    Attributes:
        all_users(dict): id пользователей
    """
    all_users: Dict[str, Any] = dict()

    def __init__(self, user_id):
        self.city = None
        self.city_id = None
        self.hotels_count = None
        self.photo_command = False
        self.photo_cnt = None
        self.photo_collection = []
        self.check_in = None
        self.check_out = None
        self.sort_flag = None
        self.flag_name = None
        self.hotels_id = []
        self.hotel_data = []
        self.max_distance = None
        self.max_price = None
        self.destination_id = None

        User.add_user(user_id, self)

    @staticmethod
    def get_user(user_id):
        if User.all_users.get(user_id) is None:
            new_user = User(user_id)
            return new_user
        return User.all_users.get(user_id)

    @classmethod
    def add_user(cls, user_id, user):
        cls.all_users[user_id] = user

    @staticmethod
    def del_user(user_id):
        if User.all_users.get(user_id) is not None:
            del User.all_users[user_id]
