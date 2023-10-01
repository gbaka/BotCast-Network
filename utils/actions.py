from random import randint
from datetime import datetime, timedelta

from pyrogram import Client, errors

from errors.custom_errors import CommandArgumentError, CommandExecutionError
from database.database_manager import DATABASE_MANAGER
from utils.autoposter import AUTOPOSTER
from utils.command_info import COMMAND_INFO
from utils import helpers, telegram_helpers
import config

"""
Этот файл содержит функции, осуществляющие основные действия,
необходимые для обработки команд пользователя.

"""


async def execute_history_command(client: Client, peer_id: int, command_part: str) -> None:
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
        record_count = DATABASE_MANAGER.history.get_record_count()
        records = list(map(str, DATABASE_MANAGER.history.get_page(page)))
        records = helpers.trim_history_records(records) if used_pattern in [("-s", int), ("-s",)] else records
        res = helpers.create_history_page(page, records, record_count)

    elif used_pattern == clear_history_pattern:
        records_count = DATABASE_MANAGER.history.get_record_count() 
        if records_count > 0:
            DATABASE_MANAGER.history.clear()
            res = ("🗑️ **История успешно очищена.\n\n**" +
                   f"Было удалено {records_count} записей.")
        else:
            res = "⚙️ **История команд и так пуста.**" 

    await client.send_message(peer_id, res)


async def execute_texts_command(client: Client, peer_id: int, command_part: str) -> None:
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
        text_id = DATABASE_MANAGER.texts.add(text)
        res = ("✅ **Текст успешно добавлен в базу.**\n\n"
              f"ID добавленного текста:  `{text_id}`")

    elif used_pattern == del_pattern:
        text_id = int(arguments_list[1])
        DATABASE_MANAGER.texts.delete(text_id)
        res = "🗑️ **Текст успешно удален из базы.**"

    elif used_pattern == clear_pattern:
        record_count = DATABASE_MANAGER.texts.get_record_count() 
        if record_count > 0:
            DATABASE_MANAGER.texts.clear()
            res = ("🗑️ **Каталог текстов успешно очищен.\n\n**" +
                   f"Было удалено {record_count} текстов.")
        else:
            res = "⚙️ **Каталог текстов и так пуст.**" 

    elif used_pattern == show_pattern:
        text_id = int(arguments_list[1])
        res = f"📝 **Текст с ID {text_id}:**\n\n"
        res += "\"" + DATABASE_MANAGER.texts.get_text(text_id).text + "\""
        pass

    elif used_pattern in get_patterns:
        record_count = DATABASE_MANAGER.texts.get_record_count() 
        page = 1 if used_pattern==() else int(arguments_list[0])
        texts = list(map(str, DATABASE_MANAGER.texts.get_page(page)))
        res = helpers.create_texts_page(page, texts, record_count)

    await client.send_message(peer_id, res)


async def execute_chats_command(client: Client, peer_id: int,  command_part: str) -> None:
    arguments_list = command_part.split()
    
    add_pattern = ("add", [str, "-this"])
    join_pattern = ("join", [str, "-this"])
    leave_pattern = ("leave", [str, "-this"])
    del_pattern = ("del", [int, "-this"])
    get_info_pattern = ("info", [str, "-this"])
    clear_pattern = ("clear",)
    get_patterns = [(), (int,)]

    patterns = [
        add_pattern,
        join_pattern,
        leave_pattern,
        del_pattern,
        get_info_pattern,
        clear_pattern,
        *get_patterns
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern in [add_pattern, del_pattern, *get_patterns]:
        deleted_chats = await telegram_helpers.chats_refresh(client)
        if deleted_chats:
            error_title = "⚠️ **С последнего применения команды боту стали недоступны следующие чаты:**"
            report = helpers.create_deleted_chats_report(deleted_chats)
            raise CommandExecutionError(report, error_title)

    if used_pattern == add_pattern:
        chat_link = peer_id if arguments_list[1] == "-this" else arguments_list[1]
        chat_details = await telegram_helpers.get_chat_details(client,chat_link)
        if not chat_details['is_participant']:
            chat_obj = await client.join_chat(chat_details["chat_link"])

            # TODO: start test block
            try:
                await telegram_helpers.mute_chat(client, chat_obj.id)
            except:
                pass
            # end test block

            print("from join_chat: \n", chat_obj)
            print("from process_chat: \n", chat_details)
            chat_id = DATABASE_MANAGER.chats.add(chat_details["title"], chat_obj.id, chat_details["members_count"] ) 
            res = ("✅ **Бот смог войти в чат и добавил его в базу.**\n\n"
                  f"ID добавленного чата:  `{chat_id}`")
        else:
            if DATABASE_MANAGER.chats.has_chat(chat_details["id"]): 
                res = "⚙️ **Чат уже добавлен в базу.**"
            else: 
                chat_id = DATABASE_MANAGER.chats.add(chat_details["title"],  chat_details["id"], chat_details["members_count"])
                res = ("✅ **Бот добавил чат в базу.**\n\n"
                      f"ID добавленного чата:  `{chat_id}`")

    elif used_pattern == join_pattern: 
        chat_link = peer_id if arguments_list[1] == "-this" else arguments_list[1]
        chat_details = await telegram_helpers.get_chat_details(client, chat_link)
        if not chat_details['is_participant']:
            chat_obj = await client.join_chat(chat_details["chat_link"])

            # TODO: start test block
            try:
                await telegram_helpers.mute_chat(client, chat_obj.id)
            except:
                pass
            # end test block

            chat_id = chat_obj.id
            print("from join_chat: \n", chat_obj)
            print("from process_chat: \n", chat_details)
            res = ("✅ **Бот успешно вошел в чат.**\n\n"
                  f"ID чата:  `{chat_id}`")
        else:
            res = "⚙️ **Бот уже находится в данном чате.**"

    elif used_pattern == leave_pattern:
        chat_link = peer_id if arguments_list[1] == "-this" else arguments_list[1]
        chat_details = await telegram_helpers.get_chat_details(client, chat_link)
        if chat_details['is_participant']:
            chat_id = chat_details['id']
            await client.leave_chat(chat_id, True)
            res = ("🗑️ **Бот успешно покинул чат.\n\n**" +
                  f"ID покинутого чата:  `{chat_id}`")
        else:
            res = "⚙️ **Бота нет в указанном чате.**"
         

    elif used_pattern == clear_pattern:
        records_count = DATABASE_MANAGER.chats.get_record_count() 
        if records_count > 0:
            DATABASE_MANAGER.chats.clear()
            res = ("🗑️ **Каталог чатов успешно очищен.\n\n**" +
                   f"Было удалено {records_count} чатов.")
        else:
            res = "⚙️ **Каталог чатов и так пуст.**" 

    elif used_pattern == del_pattern:
        chat_id = peer_id if arguments_list[1] == "-this" else int(arguments_list[1])
        DATABASE_MANAGER.chats.delete(chat_id)
        res = ("🗑️ **Чат успешно удален из базы.**\n\n"
                f"ID удаленного чата:  `{chat_id}`")

    elif used_pattern == get_info_pattern:
        chat_link = peer_id if arguments_list[1] == "-this" else  arguments_list[1]
        chat_details = await telegram_helpers.get_chat_details(client,chat_link)
        res = helpers.render_chat_info(chat_details)

    elif used_pattern in get_patterns:
        page = 1 if used_pattern==() else int(arguments_list[0])
        chats = list(map(str, DATABASE_MANAGER.chats.get_page(page)))
        record_count = DATABASE_MANAGER.chats.get_record_count()
        res = helpers.create_chats_page(page, chats, record_count)
    
    await client.send_message(peer_id, res) 


async def execute_messages_command(client: Client, peer_id: int, command_part: str) -> None:
    arguments_list = command_part.split()

    schedule_patterns = [
        ("schedule", [int, "-all", "-this"], [int, "-random"], int, int, int), 
        ("schedule", [int, "-all", "-this"], [int, "-random"], int, int,),
        ("schedule", [int, "-all", "-this"], [int, "-random"], int,)
    ]  
    autopost_patterns = [
        ("autopost", [int, "-all", "-this"], [int, "-random"], int), 
        ("autopost", [int, "-all", "-this"], [int, "-random"])
    ]
    get_patterns = [
        (), ([int, "-this"],)
    ]
    undo_pattern = ("undo", [int, "-all", "-this"])
    autopost_status_pattern = ("autopost", "status")
    autopost_stop_pattern = ("autopost", "stop")

    patterns = [
        *schedule_patterns, 
        *get_patterns,
        undo_pattern,
        *autopost_patterns,
        autopost_status_pattern,
        autopost_stop_pattern
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern in [*schedule_patterns, *get_patterns, *autopost_patterns]:
        deleted_chats = await telegram_helpers.chats_refresh(client)
        if deleted_chats:
            error_title = "⚠️ **С последнего применения команды боту стали недоступны следующие чаты:**"
            report = helpers.create_deleted_chats_report(deleted_chats)
            raise CommandExecutionError(report, error_title)
    
    if used_pattern in schedule_patterns:
        if arguments_list[1]=="-all":
            chat_objs = DATABASE_MANAGER.chats.get_chats()
            if len(chat_objs) == 0:
                raise CommandExecutionError("Вы можете добавить чаты в базу используя следующую команду:\n `/chats add`",
                                         "⚠️ **Каталог чатов пуст**")
        else:
            target_chat_id = peer_id if arguments_list[1] == "-this" else int(arguments_list[1])
            
            if not DATABASE_MANAGER.chats.has_chat(target_chat_id):   
                raise CommandExecutionError("Чтобы назначать отложенные сообщения в данный чат, добавьте его в базу следующей командой:\n`/chats add`",
                                         "⚠️ **ID указанного чата нет в базе.**")
            chat_objs=[DATABASE_MANAGER.chats.get_chat(target_chat_id)] 
        if arguments_list[2]=="-random":
            text_objs = DATABASE_MANAGER.texts.get_texts()
            if len(text_objs) == 0:
                raise CommandExecutionError("Вы можете добавить тексты в базу используя следующую команду:\n `/texts add`",
                                         "⚠️ **Каталог текстов пуст**")
        else:
            text_id = int(arguments_list[2])
            if not DATABASE_MANAGER.texts.has_text(text_id):
                raise CommandExecutionError("Чтобы просмотреть ID доступных текстов, воспользуйтесь следующей командой:\n `/texts`",
                                         "⚠️ **ID указанного текста нет в базе.**")
            text_objs = [DATABASE_MANAGER.texts.get_text(text_id)]

        messages_amount = int(arguments_list[3])
        if messages_amount > 100:
            raise CommandExecutionError("", "⚠️ **Нельзя единовременно назначать в один чат более 100 отложенных сообщений.**") 
        if messages_amount < 1:
            raise CommandExecutionError("", "⚠️ **Количество сообщений должно быть целым положительным числом.**") 
        time_difference = int(arguments_list[4]) if len(arguments_list) >=5 else config.DELAYED_MESSAGE_TIME_DIFFERENCE
        if time_difference < 1:
            raise CommandExecutionError("", "⚠️ **Задержка между сообщениями должна быть положительным числом (в минутах).**")  
        delay = int(arguments_list[5]) if len(arguments_list)>=6 else config.INITIAL_SEND_DELAY
        if delay < 1:
            raise CommandExecutionError("", "⚠️ **Дата начала отправки сообщений должна отстоять от текущей даты как минимум на одну минуту вперед**")    
        initial_schedule_date =  datetime.now() + timedelta(minutes=delay)
        schedule_date = initial_schedule_date    

        sent_messages = []
        message_sending_info = []
        all_messages_sent = True

        for chat_obj in chat_objs:
            schedule_date = initial_schedule_date    
            chat_id = chat_obj.chat_id
            chat_title = chat_obj.name
            max_available_delayd_messages = config.MAX_DELAYED_MESSAGES_PER_CHAT - DATABASE_MANAGER.messages.get_message_count_by_chat_id(chat_id)
            iterations = min(messages_amount, max_available_delayd_messages)  
            if iterations < messages_amount:  
                all_messages_sent = False
                if iterations < 0:
                    iterations = 0
         
            sent_messages_per_chat = []
            try:
                for _ in range(iterations):
                    text_obj = text_objs[randint(0, len(text_objs)-1)]
                    text = text_obj.text
                    sent_message = await client.send_message(chat_id=chat_id,text=text,schedule_date=schedule_date)
                    print(f"назначено сообщение: {sent_message.id}")
                    print(f"сообщение:\n", sent_message)
                    sent_messages_per_chat.append(sent_message)
                    schedule_date += timedelta(minutes=time_difference)
            except Exception:
                all_messages_sent = False
            finally:
                sent_messages += sent_messages_per_chat
                amount_sent_messages = len(sent_messages_per_chat)
                message_sending_info.append({
                    "chat_title": chat_title,
                    "chat_id": chat_id, 
                    "messages_amount": amount_sent_messages,
                    "end_of_sending": initial_schedule_date + (amount_sent_messages - 1) * timedelta(minutes=time_difference), 
                })
            
        DATABASE_MANAGER.messages.add_by_telegram_message_list(sent_messages)
        res = helpers.create_delayed_messages_report(message_sending_info, initial_schedule_date, time_difference, all_messages_sent)

    elif used_pattern in get_patterns: 
        records = DATABASE_MANAGER.messages.get_messages_info_by_chats()
        extended_records = []
        for record in records:
            try:
                chat_title = DATABASE_MANAGER.chats.get_name(record[0])
            except CommandArgumentError:
                chat_title = None
            extended_records.append((*record, chat_title))
        if used_pattern == ([int, "-this"],):
            chat_id = peer_id if arguments_list[0] == "-this" else int(arguments_list[0])
            if chat_id not in [record[0] for record in records]:
                res = "⚙️ **Для чата с указанным  ID нет отложенных сообещний.**"
            else:
                match_record = [extended_record for extended_record in extended_records if extended_record[0]==chat_id]
                res = helpers.render_messages_info(match_record)
        else:
            if len(records)==0:
                res = "⚙️ **Отложенных сообщений пока нет.**"
            else:
                res = helpers.render_messages_info(extended_records) 

    elif used_pattern == undo_pattern:
        if arguments_list[1] == "-all":
            delayed_message_ids_by_chat_id = DATABASE_MANAGER.messages.get_all_message_ids_by_chat_id()
            print(delayed_message_ids_by_chat_id)
            chat_amount = len(delayed_message_ids_by_chat_id)
            if chat_amount == 0:
                res = "⚙️ **Для чатов нет отложенных сообещний.**"
            else: 
                total_deleted_messages = 0
                total_delayed_messages = sum([len(delayed_message_ids_by_chat_id[chat_id]) for chat_id in delayed_message_ids_by_chat_id])
                for chat_id in delayed_message_ids_by_chat_id:
                    delayed_message_ids = delayed_message_ids_by_chat_id[chat_id]
                    delayed_message_amount = len(delayed_message_ids)
                    deleted_messages = await telegram_helpers.delete_scheduled_messages(client, chat_id, delayed_message_ids)
                    DATABASE_MANAGER.messages.delete_messages_by_ids(deleted_messages)
                    total_deleted_messages += len(deleted_messages)
                if total_deleted_messages == total_delayed_messages:
                    res = f"✅ **Отменены {total_delayed_messages}/{total_delayed_messages} сообщений.**"
                elif total_deleted_messages == 0:
                    res = (f"⚠️ **Сообщения не были отменены.**\n\n" + 
                        "Возможно, бот был исключен из всех чатов.")
                else:
                    res = (
                        f"⚠️ **Были отменены {total_deleted_messages}/{total_delayed_messages} сообщений.**\n\n" + 
                        "Боту не удалось отменить отправку некоторых сообщений. Возможно, он был удален из некоторых чатов."
                    )              
        else:
            chat_id = peer_id if arguments_list[1] == "-this" else int(arguments_list[1])
            delayed_message_ids = DATABASE_MANAGER.messages.get_message_ids_by_chat_id(chat_id)
            delayed_message_amount = len(delayed_message_ids)
            if delayed_message_amount == 0:
                res = "⚙️ **Для чата с указанным  ID нет отложенных сообещний.**"
            else: 
                deleted_messages = await telegram_helpers.delete_scheduled_messages(client, chat_id, delayed_message_ids)
                DATABASE_MANAGER.messages.delete_messages_by_ids(deleted_messages)
                if len(deleted_messages) == delayed_message_amount:
                    res = f"✅ **Отменены {delayed_message_amount}/{delayed_message_amount} сообщений.**"
                elif len(deleted_messages) == 0:
                    res = (f"⚠️ **Сообщения не были отменены.**\n\n" + 
                        "Возможно, бот был исключен из указанного чата.")
                else:
                    res = (
                        f"⚠️ **Были отменены {len(deleted_messages)}/{delayed_message_amount} сообщений.**\n\n" + 
                        "Боту не удалось отменить отправку некоторых сообщений. Возможно, во время удаления сообщений он был исключён из чата."
                    )

    elif used_pattern in autopost_patterns:
        if arguments_list[1]=="-all":
            chat_objs = DATABASE_MANAGER.chats.get_chats()
            if len(chat_objs) == 0:
                raise CommandExecutionError("Вы можете добавить чаты в базу используя следующую команду:\n `/chats add`",
                                         "⚠️ **Каталог чатов пуст**")
        else:
            target_chat_id = peer_id if arguments_list[1] == "-this" else int(arguments_list[1])
             
            if not DATABASE_MANAGER.chats.has_chat(target_chat_id):   
                raise CommandExecutionError("Чтобы начать автопостинг в данный чат, добавьте его в базу следующей командой:\n `/chats add`",
                                         "⚠️ **ID указанного чата нет в базе.**")
            chat_objs=[DATABASE_MANAGER.chats.get_chat(target_chat_id)] 
        if arguments_list[2]=="-random":
            text_objs = DATABASE_MANAGER.texts.get_texts()
            if len(text_objs) == 0:
                raise CommandExecutionError("Вы можете добавить тексты в базу используя следующую команду:\n `/texts add`",
                                         "⚠️ **Каталог текстов пуст**")
        else:
            text_id = int(arguments_list[2])
            if not DATABASE_MANAGER.texts.has_text(text_id):
                raise CommandExecutionError("Чтобы просмотреть ID доступных текстов, воспользуйтесь следующей командой:\n `/texts`",
                                         "⚠️ **ID указанного текста нет в базе.**")
            text_objs = [DATABASE_MANAGER.texts.get_text(text_id)]
        time_difference = int(arguments_list[3]) if len(arguments_list)>=4 else config.AUTOPOST_MESSAGE_TIME_DIFFERENCE
        if time_difference < 1:
            raise CommandExecutionError("", "⚠️ **Задержка между сообщениями должна быть положительным числом (в минутах).**")  
        time_difference = timedelta(minutes=time_difference)
        if AUTOPOSTER.is_active():
            res = "⚠️ **Автопостер уже запущен.**\n\nВы можете остновть его следующей командной:\n `/messages autopost stop`"
        else:
            AUTOPOSTER.start(client, chat_objs, text_objs, time_difference)
            res = helpers.create_autoposting_start_report(chat_objs,text_objs, time_difference)
    
    elif used_pattern == autopost_stop_pattern:
        if not AUTOPOSTER.is_active():
            res = "⚠️ **Автопостер не запущен.**"
        else:
            status = AUTOPOSTER.stop()
            res = helpers.create_autoposting_end_report(status)     
    
    elif used_pattern == autopost_status_pattern:
        if not AUTOPOSTER.is_active():
            res = "⚠️ **Автопостер не запущен.**"
        else:
            status = AUTOPOSTER.get_status()
            res = helpers.create_autoposting_status_report(status)

    await client.send_message(peer_id, res)


async def execute_notes_command(client: Client, peer_id: int,  command_part: str) -> None:
    arguments_list = command_part.split()
        
    get_patterns = [(), (int,)]
    add_pattern = ("add", ...)
    del_pattern = ("del", int)
    clear_pattern = ("clear",)
    set_descr_pattern = ("setdescr", int, ...)
    
    patterns = [
        add_pattern,
        del_pattern,
        clear_pattern,
        *get_patterns,
        set_descr_pattern
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern == add_pattern:
        note = helpers.remove_first_word(command_part)
        note_id = DATABASE_MANAGER.notes.add(note)
        res = ("✅ **Заметка успешно добавлена в базу.**\n\n"
              f"ID добавленной заметки:  `{note_id}`")

    elif used_pattern == del_pattern: 
        note_id = int(arguments_list[1])
        DATABASE_MANAGER.notes.delete(note_id)
        res = "🗑️ **Заметка успешно удалена из базы.**"

    elif used_pattern in get_patterns:
        page = 1 if used_pattern==() else int(arguments_list[0])
        notes = list(map(str, DATABASE_MANAGER.notes.get_page(page)))
        note_count = DATABASE_MANAGER.notes.get_notes_count()
        res = helpers.create_notes_page(page, notes, note_count)

    elif used_pattern == clear_pattern:
        note_count = DATABASE_MANAGER.notes.get_notes_count()
        if note_count > 0:
            DATABASE_MANAGER.notes.clear()
            res = ("🗑️ **Каталог заметок успешно очищен.\n\n**" +
                   f"Было удалено {note_count} заметок.")
        else: 
            res =  "⚙️ **Каталог заметок и так пуст.**" 

    elif used_pattern == set_descr_pattern:
        note_id = int(arguments_list[1])
        description = helpers.remove_first_n_words(command_part, 2)
        DATABASE_MANAGER.notes.set_description(note_id, description)
        res = "✅ **Описание заметки успешно изменено.**"
    
    await client.send_message(peer_id, res)


async def execute_users_command(client: Client, peer_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    
    move_users_patterns = [ 
        ("move", [int, "-this"], [int, "-this"], [int, "-max"]),   # откуда, куда, сколько
        ("move", [int, "-this"], [int, "-this"])
    ]

    get_info_pattern = ("info", str)

    patterns = [
        *move_users_patterns, 
        get_info_pattern
    ]     

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)      

    if used_pattern in move_users_patterns:   
        # if not DATABASE_MANAGER.chats.has_chat(source_chat_id):
        #     raise CommandExecutionError("Вы можете добавить его в базу следующей командой:\n`/chats add`",
        #                                 "⚠️ **Чат-источник не обнаржуен в базе.**")
        source_chat_id = peer_id if arguments_list[1]=="-this" else int(arguments_list[1])  
        try: 
            source_chat_details = await telegram_helpers.get_chat_details(client, source_chat_id)   
        except: 
            raise CommandExecutionError("Помните, что бот должен состоять в чате-источнике. "
                                        "Вы можете добавить его чат-источник следующей командой:\n`/chats join`",
                                        "⚠️ **Указанный ID чата некорректен.**")
        if not source_chat_details['is_participant']:
            raise CommandExecutionError("Бота нет в указаном чате. "
                                        "Вы можете добавить бота в данный чат, не добавляя чат в базу, следующей командой:\n `/chats join`",
                                        "⚠️ **Бот должен состоять в чате-источнике.**")
        
        target_chat_id = peer_id if arguments_list[2]=="-this" else int(arguments_list[2]) 
        try:
            target_chat_details = await telegram_helpers.get_chat_details(client, target_chat_id)
        except:
            raise CommandExecutionError("Помните, что бот должен состоять в целевом чате. "
                                        "Вы можете добавить его в целевой чат следующей командой:\n`/chats join`",
                                        "⚠️ **Указанный ID чата некорректен.**")
        if not target_chat_details['is_participant']:
            raise CommandExecutionError("Бота нет в указаном чате. "
                                        "Вы можете добавить бота в данный чат, не добавляя чат в базу, следующей командой:\n `/chats join`",
                                        "⚠️ **Бот должен состоять в целевом чате.**")
        
        if source_chat_id == target_chat_id:
            raise CommandExecutionError("", "⚠️ **ID чата-источника не должен совпадать с ID целевого чата.**")

        user_move_argument = arguments_list[3] if len(arguments_list) >= 4 else config.DEFAULT_USERS_TO_MOVE
        if user_move_argument == "-max":
            status = await telegram_helpers.transfer_users(client, source_chat_id, target_chat_id, config.MAX_USERS_TO_MOVE) 
        else:
            user_move_count = int(user_move_argument)
            if user_move_count > config.MAX_USERS_TO_MOVE:
                raise CommandExecutionError("", f"⚠️ **Количество переносимых участников не должно превышать {config.MAX_USERS_TO_MOVE}.**")
            if user_move_count < 1:
                 raise CommandExecutionError("", f"⚠️ **Количество переносимых участников должно быть целым положтельным числом.**")
            status = await telegram_helpers.transfer_users(client, source_chat_id, target_chat_id, user_move_count)
            
        res = helpers.create_moved_users_report(status)
       
    elif used_pattern == get_info_pattern:
        user_link = arguments_list[1]
        user_link = helpers.convert_link_to_username(user_link)
        print(user_link)
        api_error = True
        try:
            user_obj = await client.get_users(user_link)
            res = helpers.render_user_info(user_obj)
            api_error = False
        except errors.exceptions.bad_request_400.UsernameNotOccupied:
            error_title = "⚠️ **Пользователя с таким username не существует.**"
        except (errors.exceptions.bad_request_400.UsernameInvalid, IndexError, KeyError):
            error_title = "⚠️ **Имя пользователя некорректно.**"
        except errors.exceptions.bad_request_400.PeerIdInvalid:
            error_title = "⚠️ **ID пользователя некорректен.**"
        
        if api_error:
            raise CommandExecutionError("", error_title)

    await client.send_message(peer_id, str(res))


async def execute_help_command(client: Client, peer_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    
    general_help_pattern = ()
    special_help_pattern = (str,)
  
    patterns = [
        general_help_pattern,
        special_help_pattern
    ]

    used_pattern = helpers.validate_arguments_against_patterns(arguments_list, patterns)

    if used_pattern == general_help_pattern:
        title = "📝 **Справка по командам бота:**\n\n"
        res = title + COMMAND_INFO["general"]

    elif used_pattern == special_help_pattern:
        section = arguments_list[0]
        if section not in COMMAND_INFO:
            res = "⚠️ **Такого раздела команд нет.**"
        else: 
            title = f"📝 **Справка по командам секции {section}:**\n\n"
            res = title + COMMAND_INFO[section]
    
    await client.send_message(peer_id, res)


async def about(client: Client, peer_id: int, command_part: str) -> None:
    arguments_list = command_part.split()
    empty_pattern = ()
    patterns = [
        empty_pattern
    ]
    helpers.validate_arguments_against_patterns(arguments_list, patterns)

    bot_info = (
        "**BakaposterTG v.1.3.1**\n\n"

        "__**Разработчик:**__ `@itbakus` aka `Бакус` aka `Самарский Титан` aka `Киборг Ветеран Самары 2014` aka `Ъака` aka "
        "`Шварц из Самары` aka `Мистер Черноголовка 2020` aka `Cоветник губернатора Тульской области по программированию`.\n\n"

        "__**Дата последнего обнвления:**__ 01.10.2023"
    )
    try:
        await client.send_message(peer_id, bot_info)
    except:
        pass
