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
        "Неправильные типы или количество аргументов"
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

