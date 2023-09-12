from errors.custom_errors import CommandArgumentError
import re
from fuzzywuzzy import fuzz, process

"""
Этот файл содержит вспомогательные функции, используемые в 
функциях из фалйа actions.py

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


def can_convert_to_types(input_list, type_patterns):
    """
    Функция проверяет, возможно ли привести переданные 
    аргументы к определенных типам. Если при проверке
    в type_patterns встречается тип эллипсис (...), значит все последующие
    аргументы валидны.
    """
    if len(input_list) != len(type_patterns) and Ellipsis not in type_patterns:
        raise CommandArgumentError(
            "Неправильные типы или количество аргументов"
        )
    for i in range(len(type_patterns)):
        current_type = type_patterns[i]
        if current_type == Ellipsis:
            return
        try:
            current_type(input_list[i])
        except (TypeError, ValueError, IndexError):
            raise CommandArgumentError(
                "Неправильные типы или количество аргументов"
            )
    return


def remove_newline_from_strings(string_list):
    """
    функция удаляет символ новой строки у всех эементов списка, и
    если этот элемент стал пустой строкой - удаляет его.
    """
    cleaned_list = [string.replace('\n', '') for string in string_list]
    cleaned_list = [string for string in cleaned_list if string != ""]
    return cleaned_list


def remove_first_word(text):
    pattern = r'^\s*\S+'
    match = re.search(pattern, text)
    if match:
        result_text = text[match.end():]
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


def find_closest_command(existing_commands : list, user_input : str):
    closest_match = process.extractOne(user_input, existing_commands, scorer=fuzz.ratio)

    if closest_match[1] >= 45: # порог сходства 
        return closest_match[0]
    else:
        return None 

