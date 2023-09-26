from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker
from database.models import Record, Chat, Text, DelayedMessage, Note, Base
from errors.custom_errors import CommandArgumentError
from utils import helpers
import config
import datetime
from pyrogram import types


# в каждом вложенном классе методы упорядочены по принципу CRUD


class DatabaseManager:
    
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=False)  # создается интерфейс для доступа к БД
        self.metadata = Base.metadata                          # метаданные о структуре таблиц
        self.metadata.create_all(self.engine)          # создание таблиц в соответствии с метаданными
        self.Session = sessionmaker(bind=self.engine)  # создание фабрики сессий (через нее создаются сессии)

        self.history = DatabaseManager._History(self.Session)           # клас _History группирует методы для работы с историей комманд
        self.texts = DatabaseManager._Texts(self.Session)
        self.chats = DatabaseManager._Chats(self.Session)
        self.messages = DatabaseManager._Messages(self.Session)
        self.notes = DatabaseManager._Notes(self.Session)


    class _History:
        def __init__(self, Session: sessionmaker) -> None:
            self.Session = Session

        def create_record(self, user_id : int, user_name : str, command: str, command_arguments : str, status : str) -> None:
            with self.Session() as session:
                new_record = Record(
                    user_name=user_name,
                    user_id=user_id,
                    command=command,
                    command_arguments=command_arguments,
                    date=datetime.datetime.now(),
                    status=status
                )
                session.add(new_record)   # AIUI: session.add определяет, в какую таблицу нужно добавить запись,  #
                                          #       на основе класса объекта, переданного в качестве аргумента      #
                session.commit()  
                self._trim(session)       # удаялем старые записи из истории команд
               
        def get_page(self, page : int) -> list[Record]:
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            with self.Session() as session:
                records = session.query(Record
                    ).order_by(desc(Record.record_id)
                    ).offset((page-1)*config.HISTORY_PAGE_CAPACITY
                    ).limit(config.HISTORY_PAGE_CAPACITY)
            return records

        def get_record_count(self) -> int:
            with self.Session() as session:
                records_number = session.query(Record).count()   
            return records_number

        def clear(self) -> None:
            with self.Session() as session:
                session.query(Record).delete()
                session.commit()     

        def is_empty(self) -> bool:
            return not bool(self.get_record_count())
        
        def _trim(self, session):
            record_count = session.query(Record).count()
            if record_count > config.HISTORY_CAPACITY:
                records_to_delete = record_count - config.HISTORY_CAPACITY
                record_ids_to_delete = session.query(Record.record_id).order_by(Record.record_id).limit(records_to_delete)
                session.query(Record).filter(Record.record_id.in_(record_ids_to_delete)).delete()
            session.commit()
        

    class _Texts:
        def __init__(self, Session: sessionmaker) -> None:
            self.Session = Session

        def add(self, text: str) -> None:
            with self.Session() as session:
                new_record = Text(text=text)
                session.add(new_record)   # AIUI: session.add сам определяет, в какую таблицу нужно добавить запись,                            
                session.commit()  

        def get_text(self, text_id : int) -> Text:
            with self.Session() as session:
                query = session.query(Text).filter_by(text_id=text_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет текста с указанным ID.")
                record = query.one()
            return record
        
        def get_texts(self) -> list[Text]:
            with self.Session() as session:
                records = session.query(Text).all()
            return records
        
        def get_text_ids(self) -> list[int]:
            with self.Session() as session:
                records = session.query(Text).all()
            text_ids = [text_id for record_tuple in records for text_id in record_tuple]
            return text_ids
            
        def get_record_count(self) -> int:
            with self.Session() as session:
                records_number = session.query(Text).count()
            return records_number

        def get_page(self, page: int) -> list[Text]:
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            with self.Session() as session:
                records = session.query(Text
                    ).order_by(desc(Text.text_id)
                    ).offset((page-1)*config.TEXTS_PAGE_CAPACITY
                    ).limit(config.TEXTS_PAGE_CAPACITY)
            return records

        def delete(self, text_id: int) -> None:
            with self.Session() as session:
                query = session.query(Text).filter_by(text_id=text_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет текста с указанным ID.")
                query.delete()
                session.commit()

        def clear(self) -> None:
            with self.Session() as session:
                session.query(Text).delete()
                session.commit()    
        
        def has_text(self, text_id: int) -> bool:
            with self.Session() as session:
                query = session.query(Text).filter_by(text_id=text_id)
                records_number = query.count()
            return records_number != 0

        def search(self, substring: str):
            pass


    class _Chats:
        def __init__(self, Session:sessionmaker) -> None:
            self.Session = Session

        def add(self, name: str, chat_id: int, participant_count: int) -> None:
            with self.Session() as session:
                chat = Chat(
                    name=name, 
                    chat_id=chat_id, 
                    participant_count=participant_count,
                    date_added=datetime.datetime.now()
                )
                session.add(chat)                              
                session.commit()  

        def get_name(self, chat_id: int) -> str:
            with self.Session() as session:
                query = session.query(Chat.name).filter_by(chat_id=chat_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет чата с указанным ID.")
                record = query.one()
            return record[0]
        
        def get_page(self, page: int) -> list[Chat]:
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            with self.Session() as session:
                records = session.query(Chat
                    ).order_by(desc(Chat.date_added)
                    ).offset((page-1)*config.CHATS_PAGE_CAPACITY
                    ).limit(config.CHATS_PAGE_CAPACITY)
            return records
        
        def get_chat(self, chat_id: int) -> Chat: 
            with self.Session() as session:
                query = session.query(Chat).filter_by(chat_id=chat_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет чата с указанным ID.")
                record = query.one()
            return record
        
        def get_chat_ids(self) -> list[int]:
            with self.Session() as session:
                records = session.query(Chat.chat_id).all()
            chat_ids = [chat_id for record_tuple in records for chat_id in record_tuple]
            return chat_ids
        
        def get_chats(self) -> list[Chat]:
            with self.Session() as session:
                records = session.query(Chat).all()
            return records
        
        def get_record_count(self) -> int:
            with self.Session() as session:
                records_number = session.query(Chat).count()
            return records_number

        def delete(self, chat_id: int) -> None:
            with self.Session() as session:
                query = session.query(Chat).filter_by(chat_id=chat_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет чата с указанным ID.")
                query.delete()
                session.commit()

        def delete_by_ids(self, chat_ids : list[int]) -> None:
            with self.Session() as session:
                session.query(Chat).filter(Chat.chat_id.in_(chat_ids)).delete()
                session.commit()

        def clear(self) -> None:
            with self.Session() as session:
                session.query(Chat).delete()
                session.commit()
        
        def has_chat(self, chat_id: int) -> bool:
            with self.Session() as session:
                query = session.query(Chat).filter_by(chat_id=chat_id)
                records_number = query.count()
            return records_number != 0
        

    class _Messages:
        def __init__(self, Session: sessionmaker) -> None:
            self.Session =  Session

        def add(self, message_id: int, target_chat_id: int, schedule_date: datetime.datetime) -> None:
            with self.Session() as session:
                self._refresh(session)
                delayed_message = DelayedMessage(
                    message_id=message_id,
                    target_chat_id=target_chat_id, 
                    scheduled_date=schedule_date
                )
                session.add(delayed_message)                              
                session.commit()  

        def add_by_telegram_message_list(self, telegram_message_list : list[types.Message]) -> None:
            with self.Session() as session:
                self._refresh(session)
                for message in telegram_message_list:
                    delayed_message = DelayedMessage(
                        message_id=message.id, 
                        target_chat_id=message.chat.id, 
                        schedule_date=message.date,
                    )
                    session.add(delayed_message)
                session.commit()

        def get_message_count_by_chat_id(self, chat_id: int) -> int:
            with self.Session() as session: 
                self._refresh(session)
                records_number = session.query(DelayedMessage).filter_by(target_chat_id=chat_id).count()
            return records_number
        
        def get_messages_info_by_chats(self) -> list[tuple]:
            with self.Session() as session: 
                self._refresh(session)
                records = session.query(DelayedMessage.target_chat_id, func.count(DelayedMessage.message_id), func.max(DelayedMessage.schedule_date)
                                        ).group_by(DelayedMessage.target_chat_id
                                        ).order_by(func.count().desc()).all()
            return records
        
        def get_message_ids_by_chat_id(self, chat_id : int) -> list[int]:
            with self.Session() as session:
                self._refresh(session)
                records = session.query(DelayedMessage.message_id).filter_by(target_chat_id=chat_id).all()
            message_ids = [message_id for record_tuple in records for message_id in record_tuple]
            return message_ids
        
        def get_all_message_ids(self) -> list[int]:
            with self.Session() as session: 
                self._refresh(session)
                records = session.query(DelayedMessage.message_id).all()
            message_ids = [message_id for record_tuple in records for message_id in record_tuple]
            return message_ids
            
        def get_all_message_ids_by_chat_id(self) -> dict[list]:
            with self.Session() as session: 
                self._refresh(session)
                records = session.query(DelayedMessage.target_chat_id ,DelayedMessage.message_id).all()
            message_ids_by_chat_id = {}
            for chat_id, message_id in records:
                if chat_id not in message_ids_by_chat_id:
                    message_ids_by_chat_id[chat_id] = []
                message_ids_by_chat_id[chat_id].append(message_id)
            return message_ids_by_chat_id

        def delete_messages_by_chat_id(self) -> None:
            pass

        def delete_messages_by_ids(self, message_ids : list[int]) -> None: 
            with self.Session() as session:
                session.query(DelayedMessage).filter(DelayedMessage.message_id.in_(message_ids)).delete()
                session.commit()
        
        def _refresh(self, session):
            """ Удаляет неактуальные сообщения."""
            current_date = datetime.datetime.now()
            session.query(DelayedMessage).filter(DelayedMessage.schedule_date < current_date).delete()
            session.commit()

    class _Notes:
        def __init__(self, Session : sessionmaker) -> None:
            self.Session = Session
            
        def add(self, note : str) -> None:
            with self.Session() as session:
                note = Note(note=note)
                session.add(note)
                session.commit()

        def get_page(self, page: int) -> list[Note]:
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            with self.Session() as session:
                records = session.query(Note
                    ).order_by(desc(Note.note_id)
                    ).offset((page-1)*config.NOTES_PAGE_CAPACITY
                    ).limit(config.NOTES_PAGE_CAPACITY)
            return records
        
        def get_notes_count(self) -> None:
            with self.Session() as session:
                records_number  = session.query(Note).count()
            return records_number
        
        def set_description(self, note_id: int, description: str) -> None:
            with self.Session() as session:
                query = session.query(Note).filter_by(note_id=note_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет заметки с указанным ID.")
                note = query.one()
                note.description = description
                session.commit()
        
        def delete(self, note_id : int) -> None:
            with self.Session() as session:
                query = session.query(Note).filter_by(note_id=note_id)
                if query.count() == 0:
                    raise CommandArgumentError("В базе нет заметки с указанным ID.")
                query.delete()
                session.commit()
        
        def clear(self) -> None:
            with self.Session() as session:
                session.query(Note).delete()
                session.commit()

        def is_empty(self) -> bool:
            return bool(self.get_notes_count() == 0)  
            


DATABASE_MANAGER = DatabaseManager(config.CONNECT_STRING)


