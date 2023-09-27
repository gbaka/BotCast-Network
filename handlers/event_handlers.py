from pyrogram import Client, filters, types, enums

from utils import actions, helpers
from errors.custom_errors import BaseCommandError
from database.database_manager import DATABASE_MANAGER
import config


"""
Этот файл содержит обработчики различных событий.
"""


APP = Client("session", api_id=config.API_ID,
             api_hash=config.API_HASH, parse_mode=enums.ParseMode.MARKDOWN)
APP.set_parse_mode(enums.ParseMode.MARKDOWN)


@APP.on_message(filters.text)
async def message_handler(client: Client, message: types.Message):

    print("-----------------------")
    print(f"Получено сообщение: {message.text}")
    print(f"От кого: id{message.from_user.id} | {message.from_user.first_name} | @{message.from_user.username}")
    print(f"Время: {message.date}")
    print(f"ID сообщения: {message.id}")

    user_id = message.from_user.id
    user_name = message.from_user.username

    if not (user_id in config.ADMINS or user_name in config.ADMINS):
        return

    message_text = message.text
    split_message = message_text.split()
    command = split_message[0].lower()
    command_part = helpers.remove_first_word(message_text)
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name

    commands = {    
        "/about": actions.about,  
        "/history": actions.execute_history_command,
        "/texts": actions.execute_texts_command,
        "/chats": actions.execute_chats_command,
        "/messages": actions.execute_messages_command,
        "/notes" : actions.execute_notes_command,
        "/help" : actions.execute_help_command
    }

    try:
        if helpers.is_valid_command(command):
            if command in commands:
                await commands[command](client, user_id, command_part)
                DATABASE_MANAGER.history.create_record(user_id, user_first_name, command, command_part, "Выполнено")
            else:
                closest_command = helpers.find_closest_command(list(commands.keys()),command)
                if closest_command:
                    await client.send_message(chat_id=user_id,
                                              text="⚠️ **Команда не распознана.\n\n**" +
                                                   f"Возмжоно, вы имели ввиду:\n`{closest_command}`\n\n" +
                                                   f"Если это не так, воспользуйтесь командой `/commands` " +
                                                   f"для поиска нужной команды."
                                              )
                else:
                    await client.send_message(chat_id=user_id,
                                              text="⚠️ **Команда не распознана.**\n\n" +
                                                   f"Вы можете вспользоваться командой `/commands` " +
                                                   f"для поиска нужной команды."
                                              )
    except BaseCommandError as e:
        DATABASE_MANAGER.history.create_record(user_id, user_first_name, command, command_part, 
                                               e.get_status()
                                               )
        await client.send_message(chat_id=user_id,
                                  text=str(e)
                                  )
