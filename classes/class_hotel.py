from typing import Dict, Any


class Hotel:
    """ Класс Hotel, описывает отели по id
    Args:
        hotel_id(int): передается id отеля
    Attributes:
        all_hotels(dict): id отелей
    """
    all_hotels: Dict[str, Any] = dict()

    def __init__(self, hotel_id):
        self.name = None
        self.distance = None
        self.link = None
        self.command = None
        self.total_price = None

        Hotel.add_hotel(hotel_id, self)

    @staticmethod
    def get_hotel(hotel_id):
        if Hotel.all_hotels.get(hotel_id) is None:
            new_hotel = Hotel(hotel_id)
            return new_hotel
        return Hotel.all_hotels.get(hotel_id)

    @classmethod
    def add_hotel(cls, hotel_id, hotel):
        cls.all_hotels[hotel_id] = hotel

    @staticmethod
    def del_user(hotel_id):
        if Hotel.all_hotels.get(hotel_id) is not None:
            del Hotel.all_hotels[hotel_id]
