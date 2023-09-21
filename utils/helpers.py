from errors.custom_errors import CommandArgumentError, CommandExecutionError
from pyrogram import errors, client, types
import re
from fuzzywuzzy import fuzz, process
import config
import datetime
from pyrogram.enums import ChatType, ChatMemberStatus
from database import models
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
    
    Если при проверке в type_patterns встречается тип эллипсис (...), 
    значит все последующиеаргументы валидны.

    Формат паттерна: это кортеж из типов int, str или Ellipsis. Так же 
    там моожет содержаться строка, представляющая некоторый флаг. Например "-all".
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
                if flag != args_list[i].lower():   # веденный пользователем флаг нечуствителен к регистру
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
    # pattern = r'^\s*\S+'
    pattern = r'^\s*\S+\s*'
    match = re.search(pattern, text)
    if match:
        result_text = text[match.end():]  # match.end() - возвращает индекс конца совпадения
        return result_text
    else:
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
    # TODO: доделать, дополнить инфу
    title = "📝 **Информация об указанном чате:**\n\n"

    chat_id = chat_details['id'] if chat_details['id'] else "неизвестно"
    is_bot_in_chat = "да" if chat_details['is_participant'] else "нет"

    info = (f"__Название:__  {chat_details['title']}\n" +
            f"__ID чата:__  {chat_id}\n" +
            f"__Кол-во участников:__  {chat_details['members_count']}\n" + 
            f"__Состоит ли бот в чате:__  {is_bot_in_chat}\n" + 
            f"__Ссылка на чат:__  {chat_details['chat_link']}")
            
    return title + info

# def convert_to_unix_timestamp(time_str):
#     datetime_obj = datetime.strptime(time_str, "%d.%m.%Y %H:%M:%S")
#     timestamp = datetime_obj.timestamp() 
#     return int(timestamp) 


def extract_username_from_link(chat_link: str):
    regex_pattern = r"https://(?:t|telegram)\.(?:me|dog)/(joinchat/|\+)?([\w-]+)"
    match = re.search(regex_pattern, chat_link)
    if match:
        return match.group(2)
    else:
        raise CommandArgumentError("Ссылка недействительна.")
    


# TODO: доделать
def create_deleted_chats_report(deleted_chats: list[models.Chat]):
    
    report = ""
    for chat in deleted_chats:
        report += f"__Название:__  {chat.name}\n"
        report += f"__ID чата:__  {chat.chat_id}\n\n"

    remark = "__* Если вы всё же хотите выполнить команду - повторите ввод.__"
    return report + remark
    # info = (f"__название:__  {chat_obj.title}\n" +
    #          f"__ID чата:__  {chat_obj.id}\n" +
    #          f"__кол-во участников:__ {chat_obj.members_count}")
            

