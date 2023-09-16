from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database.models import Record, Chat, Text, Base
from errors.custom_errors import CommandArgumentError
import config
import datetime



class DatabaseManager:
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=True)  # создается интерфейс для доступа к БД
        self.metadata = Base.metadata                         # метаданные о структуре таблиц
        self.metadata.create_all(self.engine)          # создание таблиц в соответствии с метаданными
        self.Session = sessionmaker(bind=self.engine)  # создание фабрики сессий (через нее создаются сессии)

        self.history = DatabaseManager._History(self.Session)           # клас _History группирует методы для работы с историей комманд


    class _History:
        def __init__(self, Session) -> None:
            self.Session = Session

        def create_record(self, user_id, user_name, command, command_arguments, status):
            session = self.Session()
            new_record = Record(
                user_name=user_name,
                user_id=user_id,
                command=command,
                command_arguments=command_arguments,
                date=datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
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
            records_number = session.query(Record).delete()
            session.commit()
            session.close()

        def is_empty(self):
            return not bool(self.get_record_count())





    





# class Texts():
#     def __init__(self, Session) -> None:
#         self.Session = Session




DATABASE_MANAGER = DatabaseManager(config.CONNECT_STRING)

# Аналогичные методы для работы с классом Chat
