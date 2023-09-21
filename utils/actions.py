from pyrogram import Client, errors
from utils import helpers, telegram_helpers
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
    clear_history_pattern = ("clear",)

    patterns = [
        *get_histroy_patterns,
        clear_history_pattern
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern in get_histroy_patterns:
        if used_pattern in [(),  ("-s",)]:
            page = 1
        elif used_pattern == (int,):
            page = int(arguments_list[0])
        elif used_pattern == ("-s", int):
            page = int(arguments_list[1])
        records = list(map(str, DATABASE_MANAGER.history.get_page(page)))
        records = helpers.trim_history_records(records) if used_pattern in [("-s", int), ("-s",)] else records
        res = helpers.create_history_page(page, records)

    elif used_pattern == clear_history_pattern:
        records_count = DATABASE_MANAGER.history.get_record_count() 
        if records_count > 0:
            DATABASE_MANAGER.history.clear()
            res = ("🗑️ **История успешно очищена.\n\n**" +
                   f"Было удалено {records_count} записей.")
        else:
            res = "⚙️ **История команд и так пуста.**" 

    await client.send_message(user_id, res)


async def execute_texts_command(client: Client, user_id: int, command_part: str):
    arguments_list = command_part.split()

    get_patterns = [(), (int,)]
    add_pattern = ("add", ...)
    del_pattern = ("del", int)
    clear_pattern = ("clear",)
    show_pattern = ("show", int)

    patterns = [
        add_pattern,
        del_pattern,
        clear_pattern,
        show_pattern,
        *get_patterns
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern == add_pattern:
        text = helpers.remove_first_word(command_part)
        DATABASE_MANAGER.texts.add(text)
        res = "✅ **Текст успешно добавлен в базу.**"

    elif used_pattern == del_pattern:
        text_id = int(arguments_list[1])
        DATABASE_MANAGER.texts.delete(text_id)
        res = "🗑️ **Текст успешно удален из базы.**"

    elif used_pattern == clear_pattern:
        records_count = DATABASE_MANAGER.texts.get_record_count() 
        if records_count > 0:
            DATABASE_MANAGER.texts.clear()
            res = ("🗑️ **Каталог текстов успешно очищен.\n\n**" +
                   f"Было удалено {records_count} текстов.")
        else:
            res = "⚙️ **Каталог текстов и так пуст.**" 

    elif used_pattern == show_pattern:
        text_id = int(arguments_list[1])
        res = f"📝 **Текст с ID {text_id}:**\n\n"
        res += "\"" + DATABASE_MANAGER.texts.get_text(text_id).text + "\""
        pass

    elif used_pattern in get_patterns:
        page = 1 if used_pattern==() else int(arguments_list[0])
        texts = list(map(str, DATABASE_MANAGER.texts.get_page(page)))
        res = helpers.create_texts_page(page, texts)

    await client.send_message(user_id, res)


async def execute_chats_command(client: Client, user_id: int,  command_part: str):
    # print(DATABASE_MANAGER.chats.get_chat_ids())
    # chats = DATABASE_MANAGER.chats.get_chats()
    # chats = [(chat.chat_id, chat.name) for chat in chats]
    # print(chats)
    arguments_list = command_part.split()
    
    add_pattern = ("add", str)
    del_pattern = ("del", int)
    get_info_pattern = ("info", str)
    clear_pattern = ("clear",)
    get_patterns = [(), (int,)]

    patterns = [
        add_pattern,
        del_pattern,
        get_info_pattern,
        clear_pattern,
        *get_patterns
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    # refresh available chats
    if used_pattern not in [clear_pattern, get_info_pattern]:
        deleted_chats = await telegram_helpers.chats_refresh(client)
        if deleted_chats:
            error_title = "⚠️ **С последнего применения команды боту стали недоступны следующие чаты:**"
            report = helpers.create_deleted_chats_report(deleted_chats)
            raise CommandExecutionError(report, error_title)

    if used_pattern==add_pattern:
        chat_link = arguments_list[1]
        api_error = True
        try:
            chat_details = await telegram_helpers.get_chat_details(client,chat_link)
            if not chat_details['is_participant']:
                chat_obj = await client.join_chat(chat_details["chat_link"])
                print("from join_chat: \n", chat_obj)
                print("from process_chat: \n", chat_details)
                DATABASE_MANAGER.chats.add(chat_details["title"], chat_obj.id, chat_details["members_count"] ) 
                res = "✅ **Бот смог войти в чат и добавил его в базу.**" 
            else:
                if DATABASE_MANAGER.chats.has_chat(chat_details["id"]): 
                    res = "⚙️ **Бот уже добавлен в базу.**"
                else: 
                    DATABASE_MANAGER.chats.add(chat_details["title"],  chat_details["id"], chat_details["members_count"])
                    res = "✅ **Бот добавил чат в базу.**"
            api_error = False
            
        except errors.exceptions.flood_420.FloodWait as e:
            error_title = "⚙️ **Слишком много запросов к Telegram API.**"
            error_message =("Чтобы выполнить данную команду, подождите пожалуста " +
                            f"{helpers.extract_wait_time(str(e))} секунд.")
        if api_error:
            raise CommandExecutionError(error_message, error_title)

    elif used_pattern == clear_pattern:
        records_count = DATABASE_MANAGER.chats.get_record_count() 
        if records_count > 0:
            DATABASE_MANAGER.chats.clear()
            res = ("🗑️ **Каталог чатов успешно очищен.\n\n**" +
                   f"Было удалено {records_count} чатов.")
        else:
            res = "⚙️ **Каталог чатов и так пуст.**" 

    elif used_pattern == del_pattern:
        chat_id = int(arguments_list[1])
        DATABASE_MANAGER.chats.delete(chat_id)
        res = "🗑️ **Чат успешно удален из базы.**"

    elif used_pattern == get_info_pattern:
        chat_link = arguments_list[1]
        chat_details = await telegram_helpers.get_chat_details(client,chat_link)
        res = helpers.render_chat_info(chat_details)

    elif used_pattern in get_patterns:
        page = 1 if used_pattern==() else int(arguments_list[0])
        chats = list(map(str, DATABASE_MANAGER.chats.get_page(page)))
        res = helpers.create_chats_page(page, chats)
    
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
