import datetime

import telebot
from loguru import logger

import depends
from classes import class_user
from configuration.settings import bot, cursor, history_db


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
    bot.send_message(
        message.from_user.id,
        "Выберете интересующую Вас команду:\n\n"
    )
    bot.send_message(
        message.from_user.id,
        "Цена (сначала самая низкая) /lowprice\n"
        "Расстояние от центра города /distance\n"
        "Лучшие отзывы /best_review\n"
        "История поиска /history\n"
        "Напомнить команды /help",
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
        "*Введите название города на английском языке:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    user_ = class_user.User.get_user(user_id)
    user_.sort_flag = "price"
    user_.flag_name = "/lowprice"
    bot.register_next_step_handler(message, get_city_name)


@bot.message_handler(commands=["distance"])
def distance(message: telebot.types.Message) -> None:
    """
    Функция для получения города поиска и
    записи в класс User сортировки high_price
    :param message
    """
    user_id = message.chat.id
    logger.info("User %s chooses distance category", user_id)
    bot.send_message(
        message.chat.id,
        "*Введите название города:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    user_ = class_user.User.get_user(user_id)
    user_.sort_flag = "distance"
    user_.flag_name = "/distance"
    bot.register_next_step_handler(message, get_city_name)


@bot.message_handler(commands=["best_review"])
def best_review(message: telebot.types.Message) -> None:
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
    user_ = class_user.User.get_user(user_id)
    user_.sort_flag = "bayesian_review_score"
    user_.flag_name = "/best_review"
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
        date_output = f"{date}\n{row[1]}{row[2]}"

        bot.send_message(message.from_user.id, date_output)
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
    logger.info("User % inputs a city name", message.chat.id)

    user_id: int = message.chat.id
    city_name: str = message.text
    user_ = class_user.User.get_user(user_id)
    user_.city = city_name

    if depends.city_exists(user_id):
        get_hotels_cnt(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        logger.info(
            "User % inputs a city name that doesn't exist in API",
            message.chat.id
        )
        bot.send_message(
            message.chat.id,
            "Такого города нет. Введите другой город."
        )
        if user_.sort_flag == "price":
            low_price(message)
        elif user_.sort_flag == "distance":
            distance(message)
        else:
            best_review(message)


def get_hotels_cnt(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя количества рассматриваемых отелей
    :param message
    """
    bot.send_message(
        message.chat.id,
        "*Укажите количество вариантов, которые "
        "будут вам показаны.\nОт 1 до 10*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    logger.info("User %s inputs the number of hotels", message.chat.id)
    bot.register_next_step_handler(message, check_hotels_cnt)


def check_hotels_cnt(message: telebot.types.Message) -> None:
    """
    Функция для проверки количества отелей,
    который вводит пользователь и его записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    hotels_cnt: str = message.text
    user_ = class_user.User.get_user(user_id)

    if hotels_cnt.isdigit():
        if 1 <= int(hotels_cnt) <= 10:
            user_.hotels_count = int(hotels_cnt)
            get_checkin_date(message)
        else:
            logger.info(
                "User %s is inputting the invalid information",
                message.chat.id
            )
            bot.send_message(
                message.from_user.id,
                "Я не могу вывести такое количество фотографий."
            )
            get_hotels_cnt(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        logger.info(
            "User %s is inputting the invalid information",
            message.chat.id
        )
        bot.send_message(message.from_user.id, "Я вас не понимаю.")
        get_hotels_cnt(message)


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
    user_ = class_user.User.get_user(user_id)

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
                check_in = (
                    rf"{str(check_in[2])}-"
                    rf"{str(check_in[1])}-"
                    rf"{str(check_in[0])}"
                )
                user_.check_in = check_in
                get_checkout_date(message)
            else:
                logger.info(
                    "User %s inputs the check-in date wrongly",
                    message.chat.id
                )
                bot.send_message(message.chat.id, "Неверно введена дата!")
                get_checkin_date(message)
        except ValueError:
            logger.info(
                "User %s inputs the check-in date wrongly",
                message.chat.id
            )
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
    user_ = class_user.User.get_user(user_id)

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
                user_.check_out = check_out
                check_dates_correlation(message)
            else:
                logger.info(
                    "User %s inputs the check-out date wrongly",
                    message.chat.id
                )
                bot.send_message(message.chat.id, "Неверно введена дата!")
                get_checkout_date(message)
        except ValueError:
            logger.info(
                "User %s inputs the check-out date wrongly",
                message.chat.id
            )
            bot.send_message(message.chat.id, "Неверно введена дата!")
            get_checkin_date(message)


def check_dates_correlation(message: telebot.types.Message) -> None:
    """
    Функция, которая проверяет, чтобы дата заезда была раньше даты выезда
    :param message
    """
    user_id: int = message.chat.id
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

    if int(str(check_out - check_in)[0]) > 0:
        logger.info("User % dates correlate", message.chat.id)
        get_min_price(message)
    else:
        get_checkin_date(message)
        logger.info("User % dates dont correlate", message.chat.id)
        bot.send_message(
            message.chat.id,
            "Дата въезда должна быть раньше даты выезда.")


def get_min_price(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя минимальной цены за сутки
    :param message
    """
    logger.info("User %s is inputting the min price", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Отлично!\nТеперь введите минимальную цену за сутки в долларах:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_min_price)


def check_min_price(message: telebot.types.Message) -> None:
    """
    Функция для проверки минимальной цены за сутки,
    который вводит пользователь и ее записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    min_price: str = message.text
    user_ = class_user.User.get_user(user_id)

    if min_price.isdigit():
        user_.min_price = float(min_price)
        get_max_price(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        logger.info("User inputs minimal price wrongly", message.chat.id)
        bot.send_message(
            message.chat.id,
            "Неверно введена максимальная цена за сутки.")
        get_min_price(message)


def get_max_price(message: telebot.types.Message) -> None:
    """
    Функция для получения от пользователя максимальной цены за сутки
    :param message
    """
    logger.info("User %s inputs the max price", message.chat.id)
    bot.send_message(
        message.chat.id,
        "*Отлично!\nТеперь введите максимальную цену за сутки в долларах:*"
        "\n_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(message, check_max_price)


def check_max_price(message: telebot.types.Message) -> None:
    """
    Функция для проверки максимальной цены за сутки,
    который вводит пользователь и ее записи в класс User
    :param message
    """
    user_id: int = message.chat.id
    max_price: str = message.text
    user_ = class_user.User.get_user(user_id)

    if max_price.isdigit():
        user_.max_price = float(max_price)
        offers_output(message)
    elif message.text == "/help":
        choose_category(message)
    else:
        logger.info("User % inputs max price wrongly", message.chat.id)
        bot.send_message(
            message.chat.id,
            "Неверно введена максимальная цена за сутки.")
        get_max_price(message)


def offers_output(message: telebot.types.Message) -> None:
    """
    Функция для вывода предложений и сохранения резльтатов в бд
    :param message
    """
    user_id: int = message.chat.id
    user_ = class_user.User.get_user(user_id)

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

    if depends.search_hotels(user_id):
        for i_hotel in user_.hotel_data:
            bot.send_message(message.chat.id, i_hotel.values())
        logger.info("User % gets the output of found hotels", message.chat.id)
        input_into_db(message, check_in_output, check_out_output)
    else:
        logger.info(
            "User % doesnt get the output on the parameters given",
            message.chat.id
        )
        bot.send_message(
            message.chat.id,
            "По вашему запросу ничего не найдено. Измените критерии поиска",
        )
        choose_category(message)


def input_into_db(message: telebot.types.Message, check_in, check_out) -> None:
    user_id: int = message.chat.id
    user_ = class_user.User.get_user(user_id)
    db_result_text: str = f"\nДата: с {check_in} по {check_out}\n"

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
    logger.info("User % record is fixed in db")
    bot.send_message(
        message.from_user.id,
        "_Кликните /help, если хотите вернуться в основное меню._",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
