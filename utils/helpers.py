
from errors.custom_errors import CommandArgumentError
import re
from fuzzywuzzy import fuzz, process
import config
import datetime

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
    

def create_history_page(page : int, records : list[str]) -> str:
    if len(records) == 0:
        if page == 1:
            history_page = "📂 **История команд пуста.**"
        else:
            history_page = f"📔 **{page}-ая страница истории команд пуста.**"
    else:
        history_page = f"📔 **{page}-ая страница истории команд:**\n\n"
        remark = (
            '__* Вы можете очистить историю команд следующей командой:__\n'
            '`/history clear`'
        )
        for record in records:
            history_page += str(record) + "\n\n"
        history_page += remark
    return history_page


def create_texts_page(page : int, texts : list[str]) -> str:
    if len(texts) == 0:
        if page == 1:
            texts_page = "📂 **Каталог текстов пуст.**"
        else:
            texts_page = f"📔 **{page}-ая страница каталога текстов пуста.**"
    else:
        texts_page = f"📔 **{page}-ая страница каталога текстов:**\n\n"
        remark = (
             "* __Вы можете удалять тексты по ID или сразу очистить весь каталог с помощью команд:__\n"
             "`/texts del`\n"
             "`/texts clear`"
        )
        for text in texts:

            _text = text if len(text)<60 else text[:60] + "..."
            _text = _text + "\""
            texts_page += _text + "\n\n"
        texts_page += remark
    return texts_page


def create_chats_page(page : int, chats : list[str]) -> str:
    if len(chats) == 0:
        if page == 1:
            chats_page = "📂 **Каталог чатов пуст.**"
        else:
            chats_page = f"📔 **{page}-ая страница каталога чатов пуста.**"
    else:
        chats_page = f"📔 **{page}-ая страница каталога чатов:**\n\n"
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
                 "Не все из отложенных сообщений были успешно созданы.**\n\n")
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
        info += (f"__**Название чата:**__  {chat_title}\n" +
                 f"__**ID чата:**__  `{chat_id}`\n\n")
        if indx > config.AUTOPOST_START_REPORT_CAPACITY:
            info += f"А также еще {len(chat_obj) - indx} чатов.\n\n"
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
        info += (f"__**Название чата:**__  {chat_title}\n" + 
                 f"__**ID чата:**__  `{chat_id}`\n" + 
                 f"__**Отправелно сообщений:**__  {message_amount} шт.\n\n") 
    
        if indx > config.AUTOPOST_STATUS_REPORT_CAPACITY:
            info += f"А также еще {status['chat_amount'] - indx} чатов.\n\n"

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
        info += (f"__**Название чата:**__  {chat_title}\n" + 
                 f"__**ID чата:**__  `{chat_id}`\n" + 
                 f"__**Отправелно сообщений:**__  {message_amount} шт.\n\n") 
    
        if indx > config.AUTOPOST_END_REPORT_CAPACITY:
            info += f"А также еще {status['chat_amount'] - indx} чатов.\n\n"

    return title + general + info[:-2]


def create_notes_page(page : int, notes : list[str]) -> str:
    if len(notes) == 0:
        if page == 1:
            notes_page = "📂 **Каталог заметок пуст.**"
        else:
            notes_page = f"📔 **{page}-ая страница каталога заметок пуста.**"
    else:
        notes_page = f"📔 **{page}-ая страница каталога заметок:**\n\n"
        remark = (
             "* __Вы можете удалять заметки по ID или сразу очистить весь каталог с помощью команд:__\n"
             "`/notes del`\n"
             "`/notes clear`"
        )
        for note in notes:
            notes_page += note + "\n\n"
        notes_page += remark
    return notes_page
                              
