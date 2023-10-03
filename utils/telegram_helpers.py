from errors.custom_errors import CommandExecutionError
from database.database_manager import DATABASE_MANAGER

from pyrogram import errors, client, types
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.raw.functions.messages import DeleteScheduledMessages
from pyrogram.raw.functions.account import UpdateNotifySettings
from pyrogram.raw.types import InputPeerNotifySettings, InputNotifyPeer

import re
import datetime


async def is_bot_in_chat(client: client.Client, chat_id : int):
    bot_info = await client.get_me()
    try:
        chat_member =  await client.get_chat_member(chat_id, bot_info.id)
        if chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        return False
    except (errors.exceptions.bad_request_400.BadRequest,
             errors.exceptions.not_acceptable_406.ChannelPrivate,
             KeyError, ValueError):
        return False
    

async def get_chat_details(client: client.Client, chat_link: str):
    try:  
        chat_obj = await client.get_chat(chat_link)
        chat_type = chat_obj.type
        if chat_obj.type not in ["supergroup","group", ChatType.SUPERGROUP, ChatType.GROUP]:
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
        

# OLD VER:
# async def chats_refresh(client: client.Client):
#     """ Возвраащет список удаленных после refresh чатов (объектов модели Chat). """
#     chats = DATABASE_MANAGER.chats.get_chats()
#     chats_to_delete = []
#     for chat in chats:
#         if not await is_bot_in_chat(client, chat.chat_id):
#             chats_to_delete.append(chat)
#     chat_ids_to_delete = [chat.chat_id for chat in chats_to_delete]
#     DATABASE_MANAGER.chats.delete_by_ids(chat_ids_to_delete)
#     return chats_to_delete

# NEW VER:
async def chats_refresh(client: client.Client) -> list[int]:
    """ Возвраащет список удаленных после refresh чатов (объектов модели Chat). """

    db_chats = DATABASE_MANAGER.chats.get_chats() # chats in db format
    chat_ids = []  # current chat ids
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP, "supergroup","group"]:
            # если в возвращаемом объекте chat нет информации о количестве пользователь - бота там забанили
            if not dialog.chat.members_count: 
                continue
        chat_ids.append(dialog.chat.id)
        
    chats_to_delete = [db_chat for db_chat in db_chats if db_chat.chat_id not in chat_ids] # chats in db format
    chat_ids_to_delete = [db_chat.chat_id for db_chat in chats_to_delete]
    DATABASE_MANAGER.chats.delete_by_ids(chat_ids_to_delete)
    return chats_to_delete


async def delete_scheduled_messages(client: client.Client, chat_id : int, message_ids_to_delete : list[int]) -> list[int]:
    input_peer = await client.resolve_peer(peer_id=chat_id)
    deleted_message_ids = []

    for message_id in message_ids_to_delete:
        try:
            TLObject = DeleteScheduledMessages(peer=input_peer, id=[message_id])
            await client.invoke(TLObject)
            deleted_message_ids.append(message_id)
        except Exception: 
            break
    return deleted_message_ids


async def mute_chat(client : client.Client, chat_id : int):
    input_peer = await client.resolve_peer(peer_id=chat_id)
    input_notify_peer = InputNotifyPeer(peer=input_peer)
    now_unix_time = int(datetime.datetime.now().timestamp())
    seconds_in_year = 86400 * 365
    settings = InputPeerNotifySettings(silent=True, show_previews=False, mute_until=now_unix_time + seconds_in_year)
    TLObject = UpdateNotifySettings(peer=input_notify_peer, settings=settings)
    await client.invoke(TLObject)


async def transfer_users(client : client.Client, source_chat_id : int, target_chat_id : int, users_amount : int) -> list[types.User]:
    # print(f"amout is : {users_amount}")
    
    target_chat_user_ids = []
    async for chat_member in client.get_chat_members(chat_id=target_chat_id):
        if chat_member.user:
            user_id = chat_member.user.id
            target_chat_user_ids.append(user_id)

    added_users = []
    occured_critical_exception = None
    async for chat_member in client.get_chat_members(chat_id=source_chat_id):
        if chat_member.user:
            if chat_member.status == ChatMemberStatus.MEMBER and chat_member.user.id not in target_chat_user_ids and not chat_member.user.is_bot: 
                user = chat_member.user
                user_id = user.id
                status = False
                try:
                    status = await client.add_chat_members(target_chat_id, user_id)
                    added_users.append(user)

                # CRITICAL EXCEPTIONS: #
                except errors.exceptions.flood_420.FloodWait as e:
                    occured_critical_exception = e
                    break

                # NON CRITICAL EXCEPTIONS: #
                except Exception as e:
                    print(user_id, status, e)
                    continue
                
                if 1 <= users_amount <= len(added_users):
                    break

    return {"added_users" : added_users,
            "source_chat_id" : source_chat_id,
            "target_chat_id" : target_chat_id,
            "expected_added_user_count" : users_amount,
            "error" : occured_critical_exception} 


async def transfer_all_users(client: client.Client, source_chat_id: int, target_chat_id: int) -> bool:
    target_chat_user_ids = []
    async for chat_member in client.get_chat_members(chat_id=target_chat_id):
        if chat_member.user:
            user_id = chat_member.user.id
            target_chat_user_ids.append(user_id)

    source_chat_user_ids = []
    async for chat_member in client.get_chat_members(chat_id=source_chat_id):
        if chat_member.user:
            if chat_member.status == ChatMemberStatus.MEMBER and chat_member.user.id not in target_chat_user_ids and not chat_member.user.is_bot: 
                source_chat_user_ids.append(chat_member.user.id)

    print(len(source_chat_user_ids))

    status = await client.add_chat_members(target_chat_id, source_chat_user_ids)
    
    return status


