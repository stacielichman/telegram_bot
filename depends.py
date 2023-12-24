import datetime
import json
from typing import Any, Union

import requests

from classes import class_hotel, class_user


def get_city_id(user_id: int) -> bool:
    """
    Функция, которая возвращает True, если город есть в базе,
    False, если такого города нет
    :return: True / False
    """
    try:
        querystring = {
            "query": class_user.User.get_user(user_id).city,
            "locale": "ru_RU",
        }
        headers = {
            "X-RapidAPI-Key":
                "6480186d5bmsh168005f058f8b31p1b4d5cjsn26ab38d40e6a",
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
        }
        response = requests.get(
            "https://hotels4.p.rapidapi.com/locations/search",
            headers=headers,
            params=querystring,
        )
        location_data = json.loads(response.text)
        destination_id = \
            location_data["suggestions"][0]["entities"][0]["destinationId"]
        user = class_user.User.get_user(user_id)
        user.destination_id = destination_id
    except TypeError:
        return False
    return True


def total_cost(user_id, price: int) -> Union[str, int]:
    """
    Функция, которая возвращает общую стоимость проживания,
    если она указана в апи, иначе возвращает "не указано"
    :return: total_price
    :rtype: int
    или
    :return: цена не указана
    :rtype: str
    """
    user = class_user.User.get_user(user_id)
    check_in = user.check_in.split("-")
    check_in = datetime.date(
        int(check_in[0]),
        int(check_in[1]),
        int(check_in[2]))
    check_out = user.check_out.split("-")
    check_out = datetime.date(
        int(check_out[0]),
        int(check_out[1]),
        int(check_out[2]))
    if price != "не указано":
        total_days = (str(check_out - check_in))[0]
        return int(total_days) * int(price)
    else:
        return "цена не указана"


def get_properties(user_id) -> Any:
    """
    Функция, которая возвращает информацию по отелю
    """
    properties_url = "https://hotels4.p.rapidapi.com/properties/list"

    properties_querystring = {
        "destinationId": class_user.User.get_user(user_id).destination_id,
        "pageNumber": "1",
        "pageSize": "25",
        "checkIn": class_user.User.get_user(user_id).check_in,
        "checkOut": class_user.User.get_user(user_id).check_out,
        "adults1": "1",
        "sortOrder": class_user.User.get_user(user_id).sort_flag,
        "locale": "ru_RU",
        "currency": "USD",
    }

    headers = {
        "X-RapidAPI-Key": "6480186d5bmsh168005f058f8b31p1b4d5cjsn26ab38d40e6a",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
    }

    response = requests.request(
        "GET", properties_url, headers=headers, params=properties_querystring
    )
    if response is None:
        return False
    properties_data = json.loads(response.text)
    results = properties_data["data"]["body"]["searchResults"]["results"]
    user_ = class_user.User.get_user(user_id)

    if user_.hotels_count > len(results):
        user_.hotels_count = len(results)
    for hotel in results:
        hotel_dict: dict = {}
        name: str = hotel["name"]
        hotel_id: int = hotel["id"]
        user_.hotels_id.append(hotel_id)

        try:
            address: str = hotel["address"]["streetAddress"]
        except KeyError:
            address = "не указано"
        distance_to_center = hotel["landmarks"][0]["distance"][:-2]
        distance_to_center = distance_to_center.replace(",", ".")
        try:
            price = hotel["ratePlan"]["price"]["current"][1:]
        except KeyError:
            price = "не указано"
        hotel_ = class_hotel.Hotel.get_hotel(hotel_id)
        hotel_.price = str(price)
        hotel_.link = f"https://www.hotels.com/ho{hotel_id}"
        hotel_.check_in = class_user.User.get_user(user_id).check_in
        hotel_.check_out = class_user.User.get_user(user_id).check_out
        hotel_.command = None
        hotel_.total_price = total_cost(user_id, price)
        output_text = (
            f"Название: {name}\n"
            f"Адрес: {address}\n"
            f"Расстояние до центра: {distance_to_center}км\n"
            f"Цена за одну ночь: ${price}\n"
            f"Общая стоимость: ${hotel_.total_price}\n"
            f"Ссылка на отель: https://www.hotels.com/ho{hotel_id}"
        )
        hotel_dict["hotel_id"] = hotel_id
        hotel_dict["output_text"] = output_text

        if user_.sort_flag == "DISTANCE_FROM_LANDMARK":
            max_price = user_.max_price
            max_distance = user_.max_distance
            if price.isdigit():
                if float(price) <= float(max_price) and float(
                    distance_to_center
                ) <= float(max_distance):
                    user_.hotel_data.append(hotel_dict)
            else:
                continue
        else:
            user_.hotel_data.append(hotel_dict)
    return True


def get_photo(user_id, hotel_id: str) -> None:
    """
    Функция, которая передает ссылки фотографий в список аттрибута класса User
    :return: None
    """
    photo_url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": hotel_id}
    headers = {
        "X-RapidAPI-Key": "6480186d5bmsh168005f058f8b31p1b4d5cjsn26ab38d40e6a",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
    }
    response_photo = requests.request(
        "GET", photo_url, headers=headers, params=querystring
    )
    photo_data = json.loads(response_photo.text)

    user = class_user.User.get_user(user_id)
    if user.photo_cnt > 5:
        user.photo_cnt = 5
        if user.photo_cnt > len(photo_data["hotelImages"]):
            user.photo_cnt = len(photo_data["hotelImages"])

    for i_photo in range(user.photo_cnt):
        base_url = photo_data["hotelImages"][i_photo]["baseUrl"]
        photo_results = base_url.format(size="y")
        user.photo_collection.append(photo_results)
    return
