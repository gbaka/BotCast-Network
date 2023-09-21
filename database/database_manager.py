from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database.models import Record, Chat, Text, Base
from errors.custom_errors import CommandArgumentError
from utils import helpers
import config
import datetime

# TODO: вместо ручного открытия и закрытия сессий использовать with 


class DatabaseManager:
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=True)  # создается интерфейс для доступа к БД
        self.metadata = Base.metadata                         # метаданные о структуре таблиц
        self.metadata.create_all(self.engine)          # создание таблиц в соответствии с метаданными
        self.Session = sessionmaker(bind=self.engine)  # создание фабрики сессий (через нее создаются сессии)

        self.history = DatabaseManager._History(self.Session)           # клас _History группирует методы для работы с историей комманд
        self.texts = DatabaseManager._Texts(self.Session)
        self.chats = DatabaseManager._Chats(self.Session)


    class _History:
        def __init__(self, Session: sessionmaker) -> None:
            self.Session = Session

        def create_record(self, user_id, user_name, command, command_arguments, status):
            session = self.Session()
            new_record = Record(
                user_name=user_name,
                user_id=user_id,
                command=command,
                command_arguments=command_arguments,
                date=datetime.datetime.now(),
                status=status
            )
            session.add(new_record)   # AIUI: session.add определяет, в какую таблицу нужно добавить запись,
                                    # на основе класса объекта, переданного в качестве аргумента
            session.commit()  
            self._trim(session)  # удаялем старые записи из истории команд
            session.close()

        def get_page(self, page):
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            session = self.Session()
            records = session.query(Record
                ).order_by(desc(Record.record_id)
                ).offset((page-1)*config.HISTORY_PAGE_CAPACITY
                ).limit(config.HISTORY_PAGE_CAPACITY)
            session.close()
            return records

        def _trim(self, session):
            record_count = session.query(Record).count()
            if record_count > config.HISTORY_CAPACITY:
                records_to_delete = record_count - config.HISTORY_CAPACITY
                record_ids_to_delete = session.query(Record.record_id).order_by(Record.record_id).limit(records_to_delete)
                session.query(Record).filter(Record.record_id.in_(record_ids_to_delete)).delete()
            session.commit()

        def get_record_count(self):
            session = self.Session()
            records_number = session.query(Record).count()
            session.close()
            return records_number

        def clear(self):
            session = self.Session()
            session.query(Record).delete()
            session.commit()
            session.close()

        def is_empty(self):
            return not bool(self.get_record_count())
        

    class _Texts:
        def __init__(self, Session: sessionmaker) -> None:
            self.Session = Session

        def add(self, text: str):
            session = self.Session()
            new_record = Text(text=text)
            session.add(new_record)   # AIUI: session.add определяет, в какую таблицу нужно добавить запись,                            
            session.commit()  
            session.close()

        def get_text(self, text_id):
            session = self.Session()
            query = session.query(Text).filter_by(text_id=text_id)
            if query.count() == 0:
                raise CommandArgumentError("В базе нет текста с указанным ID.")
            session.close()
            return query.one()
        
        def get_record_count(self):
            session = self.Session()
            records_number = session.query(Text).count()
            session.close()
            return records_number

        def get_page(self, page: int):
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            session = self.Session()
            records = session.query(Text
                ).order_by(desc(Text.text_id)
                ).offset((page-1)*config.TEXTS_PAGE_CAPACITY
                ).limit(config.TEXTS_PAGE_CAPACITY)
            session.close()
            return records

        def delete(self, text_id: int):
            session = self.Session()
            query = session.query(Text).filter_by(text_id=text_id)
            if query.count() == 0:
                raise CommandArgumentError("В базе нет текста с указанным ID.")
            query.delete()
            session.commit()
            session.close()

        def clear(self):
            session = self.Session()
            session.query(Text).delete()
            session.commit()
            session.close()

        def search(self, string: str):
            pass


    class _Chats:
        def __init__(self, Session:sessionmaker) -> None:
            self.Session = Session

        def add(self, name: str, chat_id: int, participant_count: int):
            session = self.Session()
            chat = Chat(
                name=name, 
                chat_id=chat_id, 
                participant_count=participant_count,
                date_added=datetime.datetime.now()
            )
            session.add(chat)                              
            session.commit()  
            session.close()

        def delete(self, chat_id: int):
            session = self.Session()
            query = session.query(Chat).filter_by(chat_id=chat_id)
            if query.count() == 0:
                raise CommandArgumentError("В базе нет чата с указанным ID.")
            query.delete()
            session.commit()
            session.close()

        def get_page(self, page: int):
            if page < 1:
                raise CommandArgumentError("Номер страницы не может быть меньше единицы.")
            session = self.Session()
            records = session.query(Chat
                ).order_by(desc(Chat.date_added)
                ).offset((page-1)*config.CHATS_PAGE_CAPACITY
                ).limit(config.CHATS_PAGE_CAPACITY)
            session.close()
            return records
        
        def has_chat(self, chat_id: int):
            session = self.Session()
            query = session.query(Chat).filter_by(chat_id=chat_id)
            session.close()
            return query.count() != 0
        
        def clear(self):
            session = self.Session()
            session.query(Chat).delete()
            session.commit()
            session.close()

        def get_chat_ids(self) -> list[int]:
            session = self.Session()
            records = session.query(Chat.chat_id).all()
            session.close()
            chat_ids = [chat_id for record_tuple in records for chat_id in record_tuple]
            return chat_ids
        
        def get_chats(self) -> list[Chat]:
            session = self.Session()
            records = session.query(Chat).all()
            session.close()
            print(records)
            return records
        
        def get_record_count(self):
            session = self.Session()
            records_number = session.query(Chat).count()
            session.close()
            return records_number
        
        def delete_by_ids(self, chat_ids : list[int]):
            session = self.Session()
            session.query(Chat).filter(Chat.chat_id.in_(chat_ids)).delete()
            session.commit()
            session.close()

        






    





# class Texts():
#     def __init__(self, Session) -> None:
#         self.Session = Session




DATABASE_MANAGER = DatabaseManager(config.CONNECT_STRING)

# Аналогичные методы для работы с классом Chat
