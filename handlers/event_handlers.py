from pyrogram import Client, filters, types, enums
from utils import actions, helpers
import config


"""
Этот файл содержит обработчики различных событий.
"""


# TODO: добавить маппинг команд через словарь

app = Client("session", api_id=config.API_ID,
             api_hash=config.API_HASH, parse_mode=enums.ParseMode.MARKDOWN)
app.set_parse_mode(enums.ParseMode.MARKDOWN)


@app.on_message(filters.text)
async def message_handler(client: Client, message: types.Message):

    print("-----------------------")
    print(f"Получено сообщение: {message.text}")
    print(f"От кого: id{message.from_user.id} / {message.from_user.first_name} " +
          "/ @{message.from_user.username}")
    print(f"Время: {message.date}")
    message_text = message.text
    # split_message_with_newlines = message_text.split(' ')
    split_message = message_text.split()
    command = split_message[0].lower()
    command_part = helpers.remove_first_word(message_text)

    user_id = message.from_user.id
    if command == "/join":
        await actions.join_group_chat(client, user_id, command_part)
    elif command == "/about":
        await actions.show_summary(client, user_id)
    elif command == "/delay":
        await actions.schedule_message(client, user_id, command_part)
