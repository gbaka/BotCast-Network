from pyrogram import Client, filters, types, enums
from utils import actions, helpers
from errors.custom_errors import CommandArgumentError, CommandExecutionError
from database.database_manager import DATABASE_MANAGER
import config


"""
Этот файл содержит обработчики различных событий.
"""


# TODO: добавить маппинг команд через словарь

APP = Client("session", api_id=config.API_ID,
             api_hash=config.API_HASH, parse_mode=enums.ParseMode.MARKDOWN)
APP.set_parse_mode(enums.ParseMode.MARKDOWN)


@APP.on_message(filters.text)
async def message_handler(client: Client, message: types.Message):

    print("-----------------------")
    print(f"Получено сообщение: {message.text}")
    print(f"От кого: id{message.from_user.id} / {message.from_user.first_name} " +
          "/ @{message.from_user.username}")
    print(f"Время: {message.date}")

    message_text = message.text
    split_message = message_text.split()
    command = split_message[0].lower()
    command_part = helpers.remove_first_word(message_text)
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    commands = {
        "/join": actions.join_group_chat,
        "/about": actions.show_summary,
        "/delay": actions.schedule_message,
        "/history": actions.get_history
    }

    try:
        if helpers.is_valid_command(command):
            if command in commands:
                await commands[command](client, user_id, command_part)
                DATABASE_MANAGER.create_history_record(user_id,user_name, command, command_part, "Выполнено")
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
    except CommandArgumentError:
        DATABASE_MANAGER.create_history_record(user_id,user_name, command, command_part, 
                                               "Ошибка: неверные аргументы"
                                               )
        await client.send_message(chat_id=user_id,
                                  text="⚠️ **Проверьте правильность преданных аргументов.**\n\n" +
                                  "Возможно, вы передали неправильное количество аргументов " +
                                  "или аргументы, которые вы передали, имеют неправильный тип."
                                  )
    except CommandExecutionError:
        DATABASE_MANAGER.create_history_record(user_id,user_name, command, command_part,
                                                "Ошибка: неверный запрос"
                                               )
