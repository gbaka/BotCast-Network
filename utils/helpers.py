
from pyrogram import types, errors
from errors.custom_errors import CommandArgumentError
import re
from fuzzywuzzy import fuzz, process
import config
import datetime
from utils import helpers
from math import ceil

"""
Этот файл содержит вспомогательные функции, используемые в разных
частях проекта.

"""


def extract_wait_time(error_message: str) -> int:
    """
    Функция извлекает из текста ошибки FloodWait
    кол-во секунд кулдауна.
    """
    match = re.search(r'A wait of (\d+) seconds',
                      error_message)
    if match:
        wait_time_seconds = int(match.group(1))
        return wait_time_seconds


def validate_arguments_against_patterns(args_list, type_patterns):
    """
    Функция проверяет, возможно ли привести переданные 
    аргументы к определенных типам, указываемых в паттерне.
     
    На вход функция получает сразу список паттернов и возвращет тот, который
    удовлетовряет аргументам - в противном случае возбуждается исключение.
    
    Если при проверке в pattern'е встречается тип эллипсис (...), 
    значит все последующиеаргументы валидны.

    Формат паттерна: это кортеж из типов int, str или Ellipsis. Так же 
    там моожет содержаться строка, представляющая некоторый флаг. Например "-all". 
    Так же в качестве элемента паттерна может содержатся список, внутри него содержатся допустимые типы или значения 
    аргумента.
    """
    for pattern in type_patterns:
        continue_outer_loop = False
        if len(args_list) < len(pattern):    # не очень уверен в этих строчках, возможно придется убрать
            continue                         #
        if len(args_list) != len(pattern) and Ellipsis not in pattern:
            continue

        for i in range(len(pattern)):
            if isinstance(pattern[i], str):
                flag = pattern[i]
                if flag.lower() != args_list[i].lower():   # веденный пользователем флаг нечуствителен к регистру
                    continue_outer_loop = True
                    break

            elif isinstance(pattern[i], list):
                is_match = False
                for template in pattern[i]:
                    if isinstance(template, str):  # flag
                        flag = template
                        if flag==args_list[i].lower():
                            is_match = True
                            break
                    else:                           # type
                        _type = template
                        if _type == Ellipsis:
                            return pattern
                        try:
                            _type(args_list[i])
                            is_match = True
                            break
                        except (TypeError, ValueError, IndexError): 
                            pass
                if not is_match:
                    continue_outer_loop = True
                    break
                    
            else:
                _type = pattern[i]
                if _type == Ellipsis:
                    return pattern
                try:
                    _type(args_list[i])
                except (TypeError, ValueError, IndexError):  # если конвертация невозможна или аргументов меньше, чем требуется в соответствии
                    continue_outer_loop = True               # с паттерном аргументов - переходим к сверке со следующим паттерном 
                    break

        if not continue_outer_loop:
            return pattern
        
    raise CommandArgumentError(
        "Неправильные типы или количество аргументов."
    )
    

def remove_newline_from_strings(string_list):
    """
    функция удаляет символ новой строки у всех эементов списка, и
    если этот элемент стал пустой строкой - удаляет его.
    """
    cleaned_list = [string.replace('\n', '') for string in string_list]
    cleaned_list = [string for string in cleaned_list if string != ""]
    return cleaned_list


def remove_first_word(text):
    pattern = r'^\s*\S+\s*'
    match = re.search(pattern, text)
    if match:
        result_text = text[match.end():]  # match.end() - возвращает индекс конца совпадения
        return result_text
    else:
        return text
    

def remove_first_n_words(text, n):
    for _ in range(n):
        text = remove_first_word(text)
    return text
    
    
def truncate_string(input_string, n):
    if len(input_string) <= n:
        return input_string
    else:
        return input_string[:n] + "..."
    

def is_valid_command(string):
    if len(string) > 0:
        return string[0] == "/"
    return False


def find_closest_command(existing_commands : list, user_input : str) -> str | None:
    closest_match = process.extractOne(user_input, existing_commands, scorer=fuzz.ratio)

    if closest_match[1] >= config.WORD_SIMILARITY_THRESHOLD: # порог сходства 
        return closest_match[0]
    else:
        return None 
    

def create_history_page(page : int, records : list[str], records_count) -> str:
    if len(records) == 0:
        if page == 1:
            history_page = "📂 **История команд пуста.**"
        else:
            history_page = f"📔 **{page}-ая страница истории команд пуста.**"
            history_page += (f"Всего в истории __**{records_count}**__ записей и __**{ceil(records_count/config.HISTORY_PAGE_CAPACITY)}**__ непустых страниц.\n"
                             f"Максимальный вместимость всей истории команд: __**{config.HISTORY_CAPACITY}**__ записей.\n\n")
    else:
        history_page = f"📔 **{page}-ая страница истории команд:**\n\n"
        history_page += (f"Всего в истории __**{records_count}**__ записей и __**{ceil(records_count/config.HISTORY_PAGE_CAPACITY)}**__ непустых страниц.\n"
                             f"Максимальный вместимость всей истории команд: __**{config.HISTORY_CAPACITY}**__ записей.\n\n")
        remark = (
            '__* Вы можете очистить историю команд следующей командой:__\n'
            '`/history clear`'
        )
        for record in records:
            history_page += str(record) + "\n\n"
        history_page += remark
    return history_page


def create_texts_page(page : int, texts : list[str], text_count : int) -> str:
    if len(texts) == 0:
        if page == 1:
            texts_page = "📂 **Каталог текстов пуст.**"
        else:
            texts_page = f"📔 **{page}-ая страница каталога текстов пуста.**\n\n"
            texts_page += f"Всего в каталоге __**{text_count}**__ текстов и __**{ceil(text_count/config.TEXTS_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
    else:
        texts_page = f"📔 **{page}-ая страница каталога текстов:**\n\n"
        texts_page += f"Всего в каталоге __**{text_count}**__ текстов и __**{ceil(text_count/config.TEXTS_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
        remark = (
             "* __Вы можете удалять тексты по ID или сразу очистить весь каталог с помощью команд:__\n"
             "`/texts del`\n"
             "`/texts clear`"
        )
        for text in texts:
            _text = text if len(text) < config.PREVIEW_TEXT_LENGTH else text[:config.PREVIEW_TEXT_LENGTH] + "..."
            _text = _text + "\""
            texts_page += _text + "\n\n"
        texts_page += remark
    return texts_page


def create_chats_page(page : int, chats : list[str], chat_count : int) -> str:
    if len(chats) == 0:
        if page == 1:
            chats_page = "📂 **Каталог чатов пуст.**"
        else:
            chats_page = f"📔 **{page}-ая страница каталога чатов пуста.**\n\n"
            chats_page += f"Всего в каталоге __**{chat_count}**__ чатов и __**{ceil(chat_count/config.CHATS_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
    else:
        chats_page = f"📔 **{page}-ая страница каталога чатов:**\n\n"
        chats_page += f"Всего в каталоге __**{chat_count}**__ чатов и __**{ceil(chat_count/config.CHATS_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
        remark = (
             "* __Вы можете удалять чаты по ID или сразу очистить весь каталог с помощью команд:__\n"
             "`/chats del`\n"
             "`/chats clear`"
        )
        for chat in chats:
            chats_page += str(chat) + "\n\n"
        chats_page += remark
    return chats_page


def trim_history_records(records: list[str]) -> list[str]:
    trimmed_records = []
    for record in records:
        trimmed_records.append("\n".join(record.split('\n')[0:3]))
    return trimmed_records


def url_to_chatname(url):
    url = "@" + url.replace("https://t.me/", "").replace("t.me/", "")
    return url


def is_valid_telegram_url(url):
    pattern = r"^(https://t\.me/|t\.me/)[a-zA-Z0-9_]+$"
    if re.match(pattern, url):
        return True
    else:
        return False
    

def render_chat_info(chat_details):
    title = "📝 **Информация об указанном чате:**\n\n"

    chat_id = chat_details['id'] if chat_details['id'] else "неизвестно"
    is_bot_in_chat = "да" if chat_details['is_participant'] else "нет"

    try:
        int(chat_details['chat_link'])
        chat_link = "неизвестно"
    except ValueError:
        chat_link = chat_details['chat_link']

    info = (f"__**Название:**__  {chat_details['title']}\n" +
            f"__**ID чата:**__  `{chat_id}`\n" +
            f"__**Кол-во участников:**__  {chat_details['members_count']}\n" + 
            f"__**Состоит ли бот в чате:**__  {is_bot_in_chat}\n" + 
            f"__**Ссылка на чат:**__  {chat_link}")
            
    return title + info


def extract_username_from_link(chat_link: str):
    regex_pattern = r"https://(?:t|telegram)\.(?:me|dog)/(joinchat/|\+)?([\w-]+)"
    match = re.search(regex_pattern, chat_link)
    if match:
        return match.group(2)
    else:
        raise CommandArgumentError("Ссылка недействительна.") 
    

def convert_link_to_username(chat_link: str) -> str:
    regex_pattern = r"(?:https:\/\/)?(?:t|telegram)\.(?:me|dog)/([\w]+)"
    match = re.search(regex_pattern, chat_link)
    if match:
        return match.group(1)
    return chat_link


# TODO: доделать
def create_deleted_chats_report(deleted_chats):   
    report = ""
    for chat in deleted_chats:
        report += f"__**Название:**__  {chat.name}\n"
        report += f"__**ID чата:**__  `{chat.chat_id}`\n\n"

    remark = "__* Если вы всё же хотите выполнить команду - повторите ввод.__"
    return report + remark


def create_delayed_messages_report(message_sending_info: list[dict], initial_schedule_date: datetime.datetime, time_difference: int, all_messages_sent: bool):
    if all_messages_sent:
        title = "✅ **Отложенные успешно сообщения созданы:**\n\n"
    else: 
        title = ("⚠️ **Произошла ошибка Telegram API.**\n" + 
                 "Не все из отложенных сообщений были успешно созданы.\n\n")
    general = (f"__**Начало цикла отправки:**__\n{initial_schedule_date.strftime('%d.%m.%Y %H:%M:%S')}\n" +
               f"__**Интервал между сообщениями:**__\n{time_difference} мин.\n\n")
    info = "__**Чаты назначения:**__\n"  
    for indx, info_dict in enumerate(message_sending_info, start = 1):
        info += (f"__**Название чата:**__  {info_dict['chat_title']}\n" +
                 f"__**ID чата:**__  `{info_dict['chat_id']}`\n" +
                 f"__**Назначено сообщений:**__  {info_dict['messages_amount']}\n" +
                 f"__**Конец цикла отправки:**__  {info_dict['end_of_sending'].strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        if indx > config.MAX_DELAYED_MESSAGES_PER_CHAT:
            info += f"А также еще {len(message_sending_info) - indx} чатов.\n\n"
    return title + general + info[:-2]


def render_messages_info(chat_messages_tuples: list[tuple]) -> str: 
    total_messages = 0
    info = ""
    for chat_message_tuple in chat_messages_tuples:
        chat_title = chat_message_tuple[3]
        stop_date = chat_message_tuple[2]
        messages_amount = chat_message_tuple[1]
        chat_id = chat_message_tuple[0]
        info += f"__**Внимаение, данного чата нет в базе.**__\n" if chat_title == None else f"__**Название чата:**__  {chat_title}\n"
        info += (f"__**ID чата:**__  `{chat_id}`\n" +
                 f"__**Кол-во запланированных сообщений:**__  {messages_amount}\n"
                 f"__**Дата окончания цикла отправки:**__\n{stop_date.strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        total_messages += messages_amount
    
    title = "📝 **Информация о текущих отложенных сообщениях:**\n\n"
    if len(chat_messages_tuples)==1:
        total = ""    
    else:
        total = f"__**Всего запланированных сообщений:**__  {total_messages}\n\n"
    
    remark = "__* Вы можете отменить запланированные сообщения следующей командой:__\n`/messages undo`"
    return title + info + total + remark


def create_autoposting_start_report(chat_objs, texts, delay : datetime.timedelta) -> str:
    title = "✅ **Автопостинг успешно запущен:**\n\n"
    if len(texts)>1:
        general = "__**Для постинга будут использоваться случайные тексты из базы.**__\n\n"        
    else:
        text_id = texts[0].text_id
        general = f"__**Для постинга будет использован текст с ID {text_id}.**__\n"
    general += f"__**Задержка между отправляемыми сообщениями:**__  {int(delay.total_seconds() / 60)} мин.\n\n"
    info = "__**Чаты назначения:**__\n"
    for indx, chat_obj in enumerate(chat_objs, start=1):
        chat_id = chat_obj.chat_id
        chat_title = chat_obj.name
        if indx > config.AUTOPOST_START_REPORT_CAPACITY:
            info += f"А также еще {len(chat_objs) - indx + 1} чатов.\n\n"
            break
        info += (f"__**Название чата:**__  {chat_title}\n" +
                 f"__**ID чата:**__  `{chat_id}`\n\n")
        
    return title + general + info[:-2]


def create_autoposting_status_report(status : dict):
    if status["has_error"]:
        title =  "⚠️ **Автопостер активен, но во время постинга произошли некоторые ошибки:**\n\n"
    else: 
        title = "📝 **Автопостер активен:**\n\n"
        
    general = (f"__**Постинг производится по {status['chat_amount']} чатам.**__\n" +
               f"__**Задержка между сообщениями:**__  {int(status['delay'].total_seconds() / 60)} мин.\n"
               f"__**Всего отправлено {status['total_posts']} сообщений.**__\n" +
               f"__**В постинге используются {status['text_amount']} текстов.**__\n\n")
    
    info = "__**Чаты назначения:**__\n"
    for indx, chat_id in enumerate(status['chats_info'], start = 1):
        chat_title = status['chats_info'][chat_id]['chat_title']
        message_amount = status['chats_info'][chat_id]['post_amount']

        if indx > config.AUTOPOST_STATUS_REPORT_CAPACITY:
            info += f"А также еще {status['chat_amount'] - indx + 1} чатов.\n\n"
            break

        info += (f"__**Название чата:**__  {chat_title}\n" + 
                 f"__**ID чата:**__  `{chat_id}`\n" + 
                 f"__**Отправелно сообщений:**__  {message_amount} шт.\n\n") 
    
    return title + general + info[:-2]


def create_autoposting_end_report(status : dict):
    if status["has_error"]:
        title = "⚠️ **Автопостинг завершен с ошибками:**\n\n"
        title += "Возможно в процессе постинга бот был удален из некоторых чатов.\n\n"
    else: 
        title = "✅ **Автопостинг успешно завершен**\n\n"

    general = (f"__**Постинг производился по {status['chat_amount']} чатам.**__\n" +
               f"__**Всего отправлено {status['total_posts']} сообщений.**__\n" +
               f"__**В постинге использовались {status['text_amount']} текстов.**__\n\n")
    
    info = "__**Чаты назначения:**__\n"
    for indx, chat_id in enumerate(status['chats_info'], start = 1):
        chat_title = status['chats_info'][chat_id]['chat_title']
        message_amount = status['chats_info'][chat_id]['post_amount']

        if indx > config.AUTOPOST_END_REPORT_CAPACITY:
            info += f"А также еще {status['chat_amount'] - indx + 1} чатов.\n\n"
            break

        info += (f"__**Название чата:**__  {chat_title}\n" + 
                 f"__**ID чата:**__  `{chat_id}`\n" + 
                 f"__**Отправелно сообщений:**__  {message_amount} шт.\n\n") 
    
    return title + general + info[:-2]


def create_notes_page(page : int, notes : list[str], note_count : int) -> str:
    if len(notes) == 0:
        if page == 1:
            notes_page = "📂 **Каталог заметок пуст.**"
        else:
            notes_page = f"📔 **{page}-ая страница каталога заметок пуста.**\n\n"
            notes_page += f"Всего в каталоге __**{note_count}**__ заметок и __**{ceil(note_count/config.NOTES_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
    else:
        notes_page = f"📔 **{page}-ая страница каталога заметок:**\n\n"
        notes_page += f"Всего в каталоге __**{note_count}**__ заметок и __**{ceil(note_count/config.NOTES_PAGE_CAPACITY)}**__ непустых страниц.\n\n"
        remark = (
             "* __Вы можете удалять заметки по ID или сразу очистить весь каталог с помощью команд:__\n"
             "`/notes del`\n"
             "`/notes clear`"
        )
        for note in notes:
            notes_page += note + "\n\n"
        notes_page += remark
    return notes_page


def create_moved_users_report(status : dict) -> str: 
    added_user_count = len(status["added_users"])
    expected_added_user_count = status["expected_added_user_count"]

    if added_user_count == expected_added_user_count: 
        title = f"✅ **В целевой чат было добавлено {added_user_count}/{expected_added_user_count} пользователей.**\n\n"
        title += f"Бот смог перенести запрашиваемое число пользоватей из одного чата в другой.\n\n"
    else: 
        title = f"⚠️ **В целевой чат было добавлено {added_user_count}/{expected_added_user_count} пользователей.**\n\n"
        title += f"Боту не удалось перенести запрашиваемое число пользователей. Возможно, подходящих пользователей не было в чате.\n\n"
    
    error_info = "" 
    error = status["error"]
    print(error, type(error))
    if isinstance(error, errors.exceptions.flood_420.FloodWait):
        error_info += ("В процессе работы возникла критическая ошибка:\n\n"
                       "⚙️ **Слишком много запросов к Telegram API.**\nЧтобы выполнить данную команду, необходимо подождать "
                        f"{helpers.extract_wait_time(str(error))} секунд.\n\n")
        
    info = ""
    if added_user_count > 0:
        info += f"Из чата с ID {status['source_chat_id']} в чат с ID {status['target_chat_id']} были добавлены следующие пользователи:\n" 

        for indx, user in enumerate(status['added_users'], start=1):
            info += (f"__**Имя:**__  {user.first_name}\n"
                    f"__**ID:**__  {user.id}\n\n")
            if indx == config.MOVE_USERS_REPORT_CAPACITY:
                title += f"А также еще {len(status['added_users'] - indx)} пользователей."
                break
            
    return title + error_info + info


def render_user_info(user_obj : types.User): 

    def convert_none(arg):
        if arg is None: 
            return "Неизвествно"
        return arg
        
    def convert_bool(arg : bool):
        if arg:
            return "Да"
        elif arg is None:
            return "Неизвествно"
        return "Нет"
    
    def convert_datetime(arg : [datetime.datetime | None]):
        if arg:
            return arg.strftime('%d.%m.%Y %H:%M:%S')
        return "Неизвествно"

    title = "📝 **Информация об указанном пользователе:**\n\n"
    
    info = (f"__**Имя:**__  {convert_none(user_obj.first_name)}\n"
            f"__**Фамилия:**__  {convert_none(user_obj.last_name)}\n"
            f"__**Username:**__  {convert_none(user_obj.username)}\n"
            f"__**ID:**__  {convert_none(user_obj.id)}\n"
            f"__**Бот:**__  {convert_bool(user_obj.is_bot)}\n"
            f"__**Премиум аккаунт:**__  {convert_bool(user_obj.is_premium)}\n"
            f"__**Последний онлайн:**__  {convert_datetime(user_obj.last_online_date)}\n"
            )
    
    return title + info

                            
