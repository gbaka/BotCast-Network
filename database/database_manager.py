from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database.models import Record, Chat, Base
import config
import datetime


class DatabaseManager:
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=True)  # создается интерфейс для доступа к БД
        self.metadata = Base.metadata                         # метаданные о структуре таблиц
        self.metadata.create_all(self.engine)          # создание таблиц в соответствии с метаданными
        self.Session = sessionmaker(bind=self.engine)  # создание фабрики сессий (через нее создаются сессии)

    def create_history_record(self, user_id, user_name, command, command_arguments, status):
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
        self._trim_history(session)  # удаялем старые записи из истории команд
        session.close()

    def get_record(self, record_id):
        session = self.Session()
        record = session.query(Record).filter_by(id=record_id).first()
        session.close()
        return record

    def update_record(self, record_id, new_command):
        session = self.Session()
        record = session.query(Record).filter_by(id=record_id).first()
        if record:
            record.command = new_command
            session.commit()
        session.close()

    def get_all_records(self):
        session = self.Session()
        records = session.query(Record).order_by(desc(Record.record_id)).all()
        session.close()
        return records


    def _trim_history(self, session):
        # session = self.Session()
        record_count = session.query(Record).count()
        if record_count > config.HISTORY_CAPACITY:
            records_to_delete = record_count - config.HISTORY_CAPACITY
            record_ids_to_delete = session.query(Record.record_id).order_by(Record.record_id).limit(records_to_delete)
            session.query(Record).filter(Record.record_id.in_(record_ids_to_delete)).delete()
        session.commit()
        # session.close()


    def delete_record(self, record_id):
        session = self.Session()
        record = session.query(Record).filter_by(id=record_id).first()
        if record:
            session.delete(record)
            session.commit()
        session.close()


DATABASE_MANAGER = DatabaseManager(config.CONNECT_STRING)

# Аналогичные методы для работы с классом Chat
