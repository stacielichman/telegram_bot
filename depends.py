import json

import requests
from loguru import logger

from classes import class_hotel, class_user

headers = {
    "X-RapidAPI-Key": "cc891bbf63mshf870ba8dc660e97p1b5599jsn2500345ab8e3",
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
}


def city_exists(user_id: int) -> bool:
    """
    Функция, которая возвращает True, если найдены отели
    по заданным параметрам, False, если отелей нет
    :return: True / False
    """
    user_ = class_user.User.get_user(user_id)
    try:
        querystring = {"query": user_.city}
        url = "https://booking-com15.p.rapidapi.com/api/" \
              "v1/hotels/searchDestination"
        response = requests.get(
            url,
            headers=headers,
            params=querystring,
        )
        location_data = json.loads(response.text)
        destination_id: int = location_data["data"][0]["dest_id"]
        user_.destination_id = destination_id
    except KeyError:
        logger.error("The API doesn't respond")
        return False
    return True


def search_hotels(user_id: int) -> bool:
    """
    Функция, которая возвращает True, если город есть в базе,
    False, если такого города нет
    :return: True / False
    """
    try:
        dest_id: int = class_user.User.get_user(user_id).destination_id
        arrival_date: str = class_user.User.get_user(user_id).check_in
        departure_date: str = class_user.User.get_user(user_id).check_out
        price_min: int = class_user.User.get_user(user_id).min_price
        price_max: int = class_user.User.get_user(user_id).max_price
        sort_by: str = class_user.User.get_user(user_id).sort_flag

        querystring = {
            "dest_id": dest_id,
            "search_type": "CITY",
            "arrival_date": arrival_date,
            "departure_date": departure_date,
            "price_min": price_min,
            "price_max": price_max,
            "sort_by": sort_by,
            "currency_code": "USD",
        }
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        response = requests.get(url, headers=headers, params=querystring)

        hotels_data = json.loads(response.text)
        user_ = class_user.User.get_user(user_id)
        result = hotels_data["data"]["hotels"]
        hotel_ids: list = []

        for hotel in result:
            hotel_id = hotel["hotel_id"]
            hotel_ids.append(hotel_id)
        if len(hotel_ids) == 0:
            return False
        user_.hotel_ids = hotel_ids
        return hotel_details(user_id)
    except KeyError:
        logger.error("The API doesn't respond")
        return False


def hotel_details(user_id: int) -> bool:
    """
    Функция, которая создает словарь с текстом вывода
    :return: None
    """
    user_ = class_user.User.get_user(user_id)
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/getHotelDetails"

    try:
        hotel_dict: dict = {}
        for hotel_id in user_.hotel_ids:
            if len(hotel_dict) == user_.hotels_count:
                break

            hotel_ = class_hotel.Hotel.get_hotel(hotel_id)
            arrival_date: str = class_user.User.get_user(user_id).check_in
            departure_date: str = class_user.User.get_user(user_id).check_out
            querystring = {
                "hotel_id": hotel_id,
                "arrival_date": arrival_date,
                "departure_date": departure_date,
                "languagecode": "ru",
                "currency_code": "USD",
            }
            response = requests.get(url, headers=headers, params=querystring)
            result = json.loads(response.text)

            hotel_.price = int(result
                               ["data"]
                               ["product_price_breakdown"]
                               ["net_amount"]
                               ["value"]
                               )
            if user_.min_price <= hotel_.price <= user_.max_price:
                try:
                    hotel_.name = result["data"]["hotel_name"]
                except KeyError:
                    hotel_.name = "не указано"

                try:
                    hotel_.link = result["data"]["url"]
                except KeyError:
                    hotel_.link = "не указано"

                output_text = (
                    f"Название: {hotel_.name}\n"
                    f"Общая стоимость: ${hotel_.price}\n"
                    f"Ссылка на отель: {hotel_.link}"
                )
                hotel_dict[hotel_id] = output_text
        user_.hotel_data.append(hotel_dict)
        return True
    except KeyError:
        logger.error("The API doesn't respond")
        return False
