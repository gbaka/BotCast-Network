from pyrogram import Client, errors
from utils import helpers
from datetime import datetime, timedelta
from errors.custom_errors import CommandArgumentError, CommandExecutionError
from database.database_manager import DATABASE_MANAGER

"""
Этот файл содержит функции, осуществляющие основные действия,
необходимые для обработки команд пользователя.

"""
#TODO: внедрить DatabaseManager'a в процесс работы всех функций
#      возмножно придется переписать функцию валидации can_convert_to_types, 
#      так как одним и тем же функция могут задаваться аргументы в разных форматах

async def join_group_chat(client: Client, user_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    patterns = [(str,)]
    helpers.validate_arguments_against_patterns(arguments_list, patterns)  # выбрасывает исключения
    chat_link = arguments_list[0]
    try:
        await client.join_chat(chat_link)
        await client.send_message(user_id,
                                  "✅ **Бот успешно вошел в чат.**"
                                  )
        return

    except errors.bad_request_400.UserAlreadyParticipant:
        await client.send_message(user_id,
                                  "⚠️ **Похоже, бот уже состоит в данном чате.**"
                                  )

    except errors.exceptions.flood_420.FloodWait as e:
        error_message = str(e)
        await client.send_message(user_id,
                                  f"⚙️ **Слишком много запросов к Telegram API.**\n\nЧтобы выполнить данную команду, подождите пожалуста " +
                                  f"{helpers.extract_wait_time(error_message)} секунд."
                                  )

    except errors.exceptions.bad_request_400.InviteHashExpired:
        await client.send_message(user_id,
                                  "❌ **Срок действия ссылки истек или бот был заблокирован в данном чате.**"
                                  )

    except (errors.exceptions.bad_request_400.BadRequest):  # ...BadRequest - родительская ошибка для всех, обрабатываемых выше
        await client.send_message(user_id,
                                  "❌ **Ссылка недействительна.**"
                                  )
        
    raise CommandExecutionError("Команда не выполнена") 



async def schedule_message(client: Client, user_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    patterns = [(int, ...)]
    helpers.validate_arguments_against_patterns(arguments_list, patterns)
    message = helpers.remove_first_word(command_part)
    delay = int(arguments_list[0])
    send_time = datetime.now() + timedelta(seconds=delay)
    await client.send_message(chat_id=user_id,
                              text=message,
                              schedule_date=send_time
                              )
    await client.send_message(chat_id=user_id,
                              text="✅ **Отложенное сообщение создано.**"
                              )

async def execute_history_command(client: Client, user_id: int, command_part: str):
    arguments_list = command_part.split()
    
    get_histroy_patterns = [(), (int,), ("-s",), ("-s", int)]
    clear_history_patterns = [("clear",)]
    patterns = [
        *get_histroy_patterns,
        *clear_history_patterns
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern in get_histroy_patterns:
        if used_pattern in [(),  ("-s",)]:
            page = 1
        elif used_pattern == (int,):
            page = int(arguments_list[0])
        elif used_pattern == ("-s", int):
            page = int(arguments_list[1])
        records = list(map(str, DATABASE_MANAGER.get_history_page(page)))
        records = helpers.trim_history_records(records) if used_pattern in [("-s", int), ("-s",)] else records
        res = helpers.create_history_page(page, records)

    elif used_pattern in clear_history_patterns:
        records_count = DATABASE_MANAGER.get_history_record_count()
        if records_count > 0:
            DATABASE_MANAGER.clear_history()
            res = "🗑️ **История успешно очищена.**"
        else:
            res = "⚙️  **История команд и так пуста.**" 

    await client.send_message(user_id, res)


async def show_summary(client: Client, user_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    helpers.can_convert_to_types(arguments_list, ())

    bot_info = (
        "🤖 Мой Бот 1.0\n\n"
        "📝 Описание:\n"
        "Мой Бот - это умный бот, который может отвечать на ваши вопросы и предоставлять информацию о погоде.\n\n"
        "👤 Создатель:\n"
        "Имя: John Doe\n"
        "Контакт: john@example.com\n\n"
        "📚 Инструкции по использованию:\n"
        "- /start: Начать взаимодействие с ботом\n"
        "- /weather <город>: Получить текущую погоду в указанном городе\n"
        "- /help: Показать это сообщение справки\n\n"
        "🌐 Ссылки:\n"
        "Веб-сайт: https://www.example.com/bot\n"
        "Твиттер: @mybot\n\n"
        "© 2023 Мой Бот. Все права защищены."
    )
    try:
        await client.send_message(user_id, bot_info)
    except:
        pass
