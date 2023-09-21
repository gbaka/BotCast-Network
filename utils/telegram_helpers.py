from errors.custom_errors import CommandArgumentError, CommandExecutionError
from pyrogram import errors, client, types
import re
from pyrogram.enums import ChatType, ChatMemberStatus
from database.database_manager import DATABASE_MANAGER

async def is_bot_in_chat(client: client.Client, chat_id : int):
    bot_info = await client.get_me()
    try:
        chat_member =  await client.get_chat_member(chat_id, bot_info.id)
        if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        return False
    except (errors.exceptions.bad_request_400.BadRequest,
             errors.exceptions.not_acceptable_406.ChannelPrivate):
        return False


async def get_chat_details(client: client.Client, chat_link: str):
    #подредачить, у возбуждаемой ошибки должен быть правильный должен быть правильный заголовок и содеражние.
    try:  
        chat_obj = await client.get_chat(chat_link)
        chat_type = chat_obj.type
        if chat_obj.type not in ["supergroup", ChatType.SUPERGROUP]:
            raise CommandExecutionError("Должна быть указан ссылка на групповой чат.")
        
        if isinstance(chat_obj, types.ChatPreview):
            return {"chat_link" : chat_link, "is_participant" : False, "id" : None, "members_count" : chat_obj.members_count, "title" : chat_obj.title}
        else: 
            if await is_bot_in_chat(client, chat_obj.id):
                return {"chat_link" : chat_link, "is_participant" : True, "id" : chat_obj.id, "members_count" : chat_obj.members_count, "title" : chat_obj.title}
            else:
                return {"chat_link" : chat_link, "is_participant" : False, "id" : chat_obj.id, "members_count" : chat_obj.members_count, "title" : chat_obj.title}

    
    except errors.exceptions.bad_request_400.InviteHashExpired:
        raise  CommandExecutionError("Срок действия ссылки истек.")
    
    except (errors.exceptions.bad_request_400.PeerIdInvalid, 
            errors.exceptions.not_acceptable_406.ChannelPrivate):
        raise CommandExecutionError("Взаимодействовать с приватными чатами используя ID можно только в случае, если бот состоит в указанных чатах.",
                                   "⚠️ **Использование ID недопускается.**" )
    
    except KeyError:
            raise  CommandExecutionError("Скорее всего бот забанен в данном чате.")
    
    except (errors.exceptions.bad_request_400.UsernameInvalid,     # значит либо чат публичный, либо ссылка некорректна
            errors.exceptions.bad_request_400.UsernameNotOccupied):
        regex_pattern = r"(?:https:\/\/)?(?:t|telegram)\.(?:me|dog)/(joinchat/|\+)?([\w-]+)"
        match = re.search(regex_pattern, chat_link)
        if match:   # если ссылка корректна, => чат публичный
            username = "@" + match.group(2)
            try:
                chat_obj = await client.get_chat(username)
                chat_type = chat_obj.type
                print(type(chat_type))
                print(chat_obj)
                if chat_type not in ["supergroup", ChatType.SUPERGROUP]:
                    raise CommandExecutionError("Должна быть указана ссылка на групповой чат.")
                if await is_bot_in_chat(client, chat_obj.id):
                    return {"chat_link" : username, 
                            "is_participant" : True, 
                            "id" : chat_obj.id, 
                            "members_count" : chat_obj.members_count,
                            "title" : chat_obj.title}
                else: 
                    return {"chat_link" : username,
                            "is_participant" : False, 
                            "id" : chat_obj.id, 
                            "members_count" : chat_obj.members_count, 
                            "title" : chat_obj.title}
            
            
            except  (errors.exceptions.bad_request_400.BadRequest):     # значит ссылка на публичный чат некорректна.
                raise  CommandExecutionError("Ссылка недействительна.")
            
            except KeyError:
                raise  CommandExecutionError("Скорее всего бот забанен в данном чате.")

        else:  # если ссылка некорректна (несоответсвует паттерну ни публичной группы, ни приватной) - просто набор символов
            raise  CommandExecutionError("Ссылка некорректна или имя чата набрано неправильно.")
        

async def chats_refresh(client: client.Client):
    """ Возвраащет список удаленных после refresh чатов (объектов модели Chat). """
    # TODO: возможно потом придется переписать, не очень эффективно проверять каждый чат.
    chats = DATABASE_MANAGER.chats.get_chats()
    chats_to_delete = []
    for chat in chats:
        if not await is_bot_in_chat(client, chat.chat_id):
            chats_to_delete.append(chat)
    chat_ids_to_delete = [chat.chat_id for chat in chats_to_delete]
    DATABASE_MANAGER.chats.delete_by_ids(chat_ids_to_delete)
    return chats_to_delete

    