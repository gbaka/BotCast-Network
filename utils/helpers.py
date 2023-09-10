import re

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


# def extract_arguments(command_part: str, pattern: str) -> tuple:
#     """
#     Функция для извелчения аргументов из строки по
#     переданному паттерну (raw-строка формата reg-ex)
#     """
#     match = re.match(pattern, command_part)
#     if match:
#         return match.groups()
#     raise ValueError("Строка не удовлетворяет регулярному выражению")

# def can_convert_to_types(input_list, type_patterns):
#     """
#     Функция проверяет, возможно ли привести переданные
#     аргументы к определенных типам. Если при проверке
#     в type_patterns встречается тип str, значит все последующие
#     аргументы валидны.
#     """
#     if len(input_list) < len(type_patterns):
#         return False
#     for i in range(len(input_list)):
#         current_type = type_patterns[i]
#         if current_type == str:
#             return True
#         try:
#             current_type(input_list[i])
#         except (TypeError, ValueError):
#             return False
#     return True

def can_convert_to_types(input_list, type_patterns):
    """
    Функция проверяет, возможно ли привести переданные 
    аргументы к определенных типам. Если при проверке
    в type_patterns встречается тип эллипсис (...), значит все последующие
    аргументы валидны.
    """
    if len(input_list) != len(type_patterns) and Ellipsis not in type_patterns:
        return False
    for i in range(len(input_list)):
        current_type = type_patterns[i]
        if current_type == Ellipsis:
            return True
        try:
            current_type(input_list[i])
        except (TypeError, ValueError):
            return False
    return True


def remove_newline_from_strings(string_list):
    """
    функция удаляет символ новой строки у всех эементов списка, и
    если этот элемент стал пустой строкой - удаляет его.
    """
    cleaned_list = [string.replace('\n', '') for string in string_list]
    cleaned_list = [string for string in cleaned_list if string != ""]
    return cleaned_list


# def remove_first_word(string):
#     cleaned_string = " ".join(string.split(" ")[1:])
#     return cleaned_string

def remove_first_word(text):
    pattern = r'^\s*\S+'
    match = re.search(pattern, text)
    if match:
        result_text = text[match.end():]
        return result_text
    else:
        return text
