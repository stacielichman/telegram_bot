import datetime

import telebot
from loguru import logger
from telebot.types import InputMediaPhoto

import depends
from classes import class_hotel, class_user
from configuration.bot_token import TOKEN
from configuration.mysql_config import HISTORY_DB

logger.add(
    "logs/log.log",
    rotation="1 day",
    level="INFO",
    format="{time}{level}{message}",
    backtrace=True,
    diagnose=True,
)

history_db = HISTORY_DB
cursor = history_db.cursor()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message) -> None:
    logger.info("User %s started the bot", message.chat.id)
    bot.send_message(
        message.chat.id,
        "Привет! Я бот Too Easy Travel!\n"
        "Я могу помочь подобрать отели и хостелы "
        "для Вас.\n\nДля получения информации о доступных "
        "командах введите или кликните \n/help",
    )


@bot.message_handler(commands=["help"])
def choose_category(message: telebot.types.Message) -> None:
    logger.info("User %s is choosing a category", message.chat.id)
    bot.send_message(message.from_user.id,
                     "Выберете интересующую Вас команду:\n\n")
    bot.send_message(
        message.from_user.id,
        "Топ самых дешёвых отелей в городе /lowprice\n"
        "Топ самых дорогих отелей в городе /highprice\n"
        "Лучшее предложение для Вас /bestdeal\n"
        "История поиска /history\nНапомнить команды /help",
    )


@bot.message_handler(commands=["lowprice"])
def low_price(message: telebot.types.Message) -> None:
    """
    Функция для получения города поиска и
    записи в класс User сортировки low_price
    :param message
    """
    user_id: int = message.chat.id
    logger.info("User %s chooses low-price category", user_id)
    bot.send_message(
        message.chat.id,
        "*Введите название города:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    user = class_user.User.get_user(user_id)
    user.sort_flag = "PRICE"
    user.flag_name = "/lowprice"
    bot.register_next_step_handler(message, get_city_name)


@bot.message_handler(commands=["highprice"])
def high_price(message: telebot.types.Message) -> None:
    """
    Функция для получения города поиска и
    записи в класс User сортировки high_price
    :param message
    """
    user_id = message.chat.id
    logger.info("User %s chooses high_price category", user_id)
    bot.send_message(
        message.chat.id,
        "*Введите название города:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    user = class_user.User.get_user(user_id)
    user.sort_flag = "PRICE_HIGHEST_FIRST"
    user.flag_name = "/highprice"
    bot.register_next_step_handler(message, get_city_name)


@bot.message_handler(commands=["bestdeal"])
def bestdeal(message: telebot.types.Message) -> None:
    """
    Функция для получения города поиска и
    записи в класс User сортировки bestdeal
    :param message
    """
    user_id = message.chat.id
    logger.info("User %s chooses best_deal category", user_id)
    bot.send_message(
        message.chat.id,
        "*Введите название города:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    user = class_user.User.get_user(user_id)
    user.sort_flag = "DISTANCE_FROM_LANDMARK"
    user.flag_name = "/bestdeal"
    bot.register_next_step_handler(message, get_city_name)


@bot.message_handler(commands=["history"])
def get_history(message: telebot.types.Message) -> None:
    """
    Функция для вывода истории поиска
    :param message
    """
    logger.info("User %s chooses history category", message.chat.id)
    select_all_rows = (
        f"SELECT `date`, `command`, `result` FROM `history` "
        f"WHERE `user_id` = {message.chat.id} ORDER BY `date` LIMIT 10"
    )
    cursor.execute(select_all_rows)
    result = cursor.fetchall()

    for row in result:
        time_date = str(row[0])
        date = time_date[:10].split("-")
        date = (
            rf"{str(date[2])}."
            rf"{str(date[1])}."
            rf"{str(date[0])}  {time_date[11:20]}"
        )
        row_output = f"{date}\n{row[1]}{row[2]}"

        bot.send_message(message.from_user.id, row_output)
    bot.send_message(
        message.from_user.id,
        "_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )


def get_city_name(message: telebot.types.Message) -> None:
    """
    Функция для проверки города,
    который вводит пользователь и его записи в класс User
    :param message
    """
    logger.info("The existence of the input city is being checked")

    user_id: int = message.chat.id
    city_name: str = message.text
    user_ = class_user.User.get_user(user_id)
    user_.city = city_name

    if depends.get_city_id(user_id):
        get_hotels_cnt(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(message.chat.id,
                         "Такого города нет. Введите другой город.")
        if user_.sort_flag == "PRICE":
            low_price(message)
        elif user_.sort_flag == "PRICE_HIGHEST_FIRST":
            high_price(message)
        else:
            bestdeal(message)


def get_hotels_cnt(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя количества рассматриваемых отелей
    :param message
    """
    logger.info("User %s is inputting the number of hotels", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Укажите количество вариантов, которые "
        "будут вам показаны.\nОт 1 до 10*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_hotels_cnt)


def check_hotels_cnt(message: telebot.types.Message) -> None:
    """
    Функция для проверки количества отелей,
    который вводит пользователь и его записи в класс User
    :param message
    """
    logger.info("The validity of the input hotels count is being checked")
    user_id = message.chat.id
    hotels_cnt = message.text

    if hotels_cnt.isdigit():
        if 1 <= int(hotels_cnt) <= 10:
            user = class_user.User.get_user(user_id)
            user.hotels_count = int(hotels_cnt)
            get_photo(message)
        else:
            bot.send_message(
                message.from_user.id,
                "Я не могу вывести такое количество фотографий."
            )
            get_hotels_cnt(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(message.from_user.id, "Я вас не понимаю.")
        get_hotels_cnt(message)


def get_photo(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя информации
    о необходимости вывода фотографий
    :param message
    """
    logger.info("User %s decides if photos have to be shown", message.chat.id)
    bot.send_message(
        message.from_user.id,
        "*Показать изображаения отелей?\nВведите: да / нет.*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_get_photo)


def check_get_photo(message: telebot.types.Message) -> None:
    """
    Функция для проверки необходимости вывода фотографий,
    который вводит пользователь, и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    user = class_user.User.get_user(user_id)
    logger.info(
        "The validity of the input information "
        "if to get photos is being checked"
    )

    if message.text.lower() == "да":
        user.photo_command = True
        get_photo_count(message)
    elif message.text.lower() == "нет":
        bot.send_message(message.from_user.id, "Хорошо! Фотогафии не выводим.")
        get_checkin_date(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(message.from_user.id, "Вы неправильно ввели команду!")
        get_photo(message)


def get_photo_count(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя количества выводимых фотографий
    :param message
    """
    logger.info(
        "User %s is inputting the number "
        "of photos to be displayed", message.chat.id
    )
    bot.send_message(
        message.chat.id,
        "*Сколько выводить фотографий?\n"
        "Введите число от 1 до 5*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_photo_count)


def check_photo_count(message: telebot.types.Message) -> None:
    """
    Функция для проверки количества выводимых фотографий,
    который вводит пользователь и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    photo_count = message.text
    user = class_user.User.get_user(user_id)
    logger.info("The validity of the input count of photos is being checked")

    if photo_count.isdigit():
        if 1 <= int(photo_count) <= 5:
            user.photo_cnt = int(photo_count)
            get_checkin_date(message)
        else:
            bot.send_message(
                message.chat.id,
                "Я не могу вывести такое количество фотографий."
            )
            get_photo_count(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(message.from_user.id, "Вы неправильно ввели команду!")
        get_photo_count(message)


def get_checkin_date(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя даты заезда
    :param message
    """
    logger.info("User %s is inputting the check-in date", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Введите дату заезда через точку(день.месяц.год):*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_checkin_date)


def check_checkin_date(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя даты заезда,
    который вводит пользователь и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    check_in = message.text
    logger.info("The validity of the check-in date is being checked")

    if message.text == "/help":
        choose_category(message)
    else:
        try:
            check_in = check_in.split(".")
            if len(str(check_in[0])) == 1:
                check_in[0] = "0" + str(check_in[0])
            if (
                1 <= int(check_in[0]) <= 31
                and 1 <= int(check_in[1]) <= 12
                and int(check_in[2]) >= 2022
            ):
                check_in = \
                    rf"{str(check_in[2])}-" \
                    rf"{str(check_in[1])}-" \
                    rf"{str(check_in[0])}"
                class_user.User.get_user(user_id).check_in = check_in
                get_checkout_date(message)
            else:
                bot.send_message(message.chat.id, "Неверно введена дата!")
                get_checkin_date(message)
        except ValueError:
            bot.send_message(message.chat.id, "Неверно введена дата!")
            get_checkin_date(message)


def get_checkout_date(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя даты выезда
    :param message
    """
    logger.info("User %s is inputting the check-in date", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Введите дату выезда через точку(день.месяц.год):*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_checkout_date)


def check_checkout_date(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя даты выезда,
    который вводит пользователь и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    check_out = message.text
    logger.info("The validity of the check-out date is being checked")

    if message.text == "/help":
        choose_category(message)
    else:
        try:
            check_out = check_out.split(".")
            if len(str(check_out[0])) == 1:
                check_out[0] = "0" + str(check_out[0])
            if (
                1 <= int(check_out[0]) <= 31
                and 1 <= int(check_out[1]) <= 12
                and int(check_out[2]) >= 2022
            ):
                check_out = (
                    rf"{str(check_out[2])}-"
                    rf"{str(check_out[1])}-"
                    rf"{str(check_out[0])}"
                )
                class_user.User.get_user(user_id).check_out = check_out
                check_dates_correlation(message)
            else:
                bot.send_message(message.chat.id, "Неверно введена дата!")
                get_checkout_date(message)
        except ValueError:
            bot.send_message(message.chat.id, "Неверно введена дата!")
            get_checkin_date(message)


def check_dates_correlation(message: telebot.types.Message) -> None:
    """
    Функция, которая проверяет, чтобы дата заезда была раньше даты выезда
    :param message
    """
    user_id: int = message.chat.id
    logger.info("The correlation of the check-in and check-out "
                "dates is being checked")
    user = class_user.User.get_user(user_id)

    check_in = class_user.User.get_user(user_id).check_in.split("-")
    check_in = datetime.date(
        int(check_in[0]),
        int(check_in[1]),
        int(check_in[2]))

    check_out = class_user.User.get_user(user_id).check_out.split("-")
    check_out = datetime.date(
        int(check_out[0]),
        int(check_out[1]),
        int(check_out[2]))

    if int(str(check_out - check_in)[0]) > 0:
        if user.sort_flag == "DISTANCE_FROM_LANDMARK":
            get_max_price(message)
        else:
            offers_output(message)
    else:
        get_checkin_date(message)
        bot.send_message(
            message.chat.id,
            "The check-in date must be earlier than the check-out date"
        )


def get_max_price(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя максимальной цены за сутки
    :param message
    """
    logger.info("User %s is inputting the max price", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Отлично!\nТеперь введите максимальную цену за сутки в долларах:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_max_price)


def check_max_price(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя максимальной цены за сутки,
    который вводит пользователь и ее записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    max_price: str = message.text
    user = class_user.User.get_user(user_id)

    if max_price.isdigit():
        user.max_price = float(max_price)
        get_max_distance(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(message.chat.id,
                         "Неверно введена максимальная цена за сутки.")
        get_max_price(message)


def get_max_distance(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя максимального расстояния от центра
    :param message
    """
    logger.info(
        "User %s is inputting "
        "the max distance from the city center", message.chat.id
    )
    bot.send_message(
        message.chat.id,
        "*Хорошо.\nТеперь введите максимальное\nрасстояние "
        "от центра города(в км):*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_max_distance)


def check_max_distance(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя максимального расстояния от центра,
    который вводит пользователь, и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    logger.info("The validity of the max distance is being checked")
    max_distance = message.text

    if max_distance.isdigit():
        class_user.User.get_user(user_id).max_distance = float(max_distance)
        offers_output(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        bot.send_message(
            message.chat.id,
            "Неверно введено максимальное расстояние от центра."
        )
        get_max_distance(message)


def offers_output(message: telebot.types.Message) -> None:
    """
    Функция для вывода предложений и сохранения резльтатов в бд
    :param message
    """
    user_id: int = message.chat.id
    logger.info("The offers are being provided")
    user_ = class_user.User.get_user(user_id)
    hotel_ = class_hotel.Hotel.get_hotel

    check_in_output = user_.check_in.split("-")
    check_in_output = (
        rf"{str(check_in_output[2])}."
        rf"{str(check_in_output[1])}."
        rf"{str(check_in_output[0])}"
    )
    check_out_output = user_.check_out.split("-")
    check_out_output = (
        rf"{str(check_out_output[2])}."
        rf"{str(check_out_output[1])}."
        rf"{str(check_out_output[0])}"
    )
    bot.send_message(
        message.chat.id,
        f"Город: *{user_.city.capitalize()}*"
        f"\nКоличество отелей: *{user_.hotels_count}*"
        f"\nДата: *с {check_in_output} по {check_out_output}*",
        parse_mode="Markdown",
    )
    bot.send_message(message.chat.id, "Ищу предложения по Вашему запросу ...")

    if user_.hotels_count == 0:
        bot.send_message(
            message.chat.id,
            "По вашему запросу ничего не найдено. Измените критерии поиска",
        )
    else:
        if user_.hotels_count > len(user_.hotel_data):
            user_.hotels_count = len(user_.hotel_data)
        db_result_text = f"\nДата: с {check_in_output} по {check_out_output}\n"
        for i_hotel in range(int(user_.hotels_count)):
            output_text = user_.hotel_data[i_hotel]["output_text"]
            hotel_id = hotel_(user_.hotel_data[i_hotel]['hotel_id'])
            db_result_text += (
                f"\nОтель {i_hotel + 1}\n"
                f"Цена: ${hotel_id.total_price}\n"
                f"Ссылка: {hotel_id.link}\n"
            )
            if user_.photo_command is True:
                hotel_id = user_.hotel_data[i_hotel]["hotel_id"]
                depends.get_photo(user_id, hotel_id)
                media = []
                for i_photo in range(user_.photo_cnt):
                    if i_photo == 0:
                        media.append(
                            InputMediaPhoto(
                                user_.photo_collection[i_photo],
                                caption=output_text
                            )
                        )
                    else:
                        media.append(
                            InputMediaPhoto(user_.photo_collection[i_photo])
                        )
                bot.send_media_group(message.chat.id, media)
                user_.photo_collection = []
            else:
                bot.send_message(message.chat.id, output_text)

        sql = (
            f"INSERT INTO `history`"
            f"(`user_id`, "
            f"`result`, "
            f"`date`, "
            f"`command`"
            f")"
            f"VALUES("
            f"{message.chat.id},"
            f"'{db_result_text}', "
            f"NOW(),"
            f"'Команда: {user_.flag_name}'"
            f")"
        )
        cursor.execute(sql)
        history_db.commit()
    bot.send_message(
        message.from_user.id,
        "_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
