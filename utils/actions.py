from pyrogram import Client, errors
from . import helpers
from datetime import datetime, timedelta


"""
Этот файл содержит функции, осуществляющие основные действия,
необходимые для обработки команд пользователя.

"""


async def join_group_chat(client: Client, user_id: int, command_part: str) -> None:
    splited_command_part = command_part.split()
    if helpers.can_convert_to_types(splited_command_part, (str,)):
        chat_link = splited_command_part[0]
        try:
            await client.join_chat(chat_link)
            await client.send_message(user_id,
                                      "✅ **Бот успешно вошел в чат.**"
                                      )

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

        except errors.exceptions.bad_request_400.UsernameInvalid:
            await client.send_message(user_id,
                                      "❌ **Ссылка недействительна.**"
                                      )
    else:
        await client.send_message(chat_id=user_id,
                                  text="⚠️ **Проверьте правильность преданных аргументов.**\n\n" +
                                  "Возможно, вы передали неправильное количество аргументов " +
                                  "или аргументы, которые вы передали, имеют неправильный тип."
                                  )


async def schedule_message(client: Client, user_id: int, command_part: str) -> None:

    # splited_command_part = helpers.remove_newline_from_strings(command_part)
    splited_command_part = command_part.split()

    if helpers.can_convert_to_types(splited_command_part, (int, ...)):
        message = helpers.remove_first_word(command_part)
        # command_part_with_newlines = command_part.split(" ")

        delay = int(splited_command_part[0])
        # message = " ".join(command_part_with_newlines[1:])
        send_time = datetime.now() + timedelta(seconds=delay)
        await client.send_message(chat_id=user_id,
                                  text=message,
                                  schedule_date=send_time
                                  )
        await client.send_message(chat_id=user_id,
                                  text="✅ **Отложенное сообщение создано.**"
                                  )
    else:
        await client.send_message(chat_id=user_id,
                                  text="⚠️ **Проверьте правильность преданных аргументов.**\n\n" +
                                       "Возможно, вы передали неправильное количество аргументов " +
                                       "или аргументы, которые вы передали, имеют неправильный тип."
                                  )


async def show_summary(client: Client, user_id: int) -> None:
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
