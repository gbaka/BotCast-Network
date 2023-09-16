# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from utils import helpers

"""
Тут объявляются классы, соответствующие таблицам из БД.

Метаданные o структуре таблиц и их атрибутах записиваются
в Base.metdata, далее объект Base импортируется в database_manager.py
и используюется там для инициализации таблиц внутри класса DatabaseManager.
"""

Base = declarative_base()


class Record(Base):
    __tablename__ = 'history'
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    user_name = Column(Integer)
    command = Column(String)
    command_arguments = Column(String)
    date = Column(String)
    status = Column(String)

    def __str__(self):
        return (f"__Команда:__  `{self.command}`\n" +
                f"__Аргументы:__  `{helpers.truncate_string(self.command_arguments, 16)}`\n" +
                f"__Дата:__  {self.date}\n" +
                f"__Имя пользователя:__  {helpers.truncate_string(self.user_name, 12)}\n" +
                f"__ID пользователя:__  {self.user_id}\n" +
                f"__Статус:__  {self.status}")
    


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    chat_name = Column(String)
    description = Column(String)


class Text(Base):
    __tablename__ = 'texts'

    text_id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)

    def __str__(self):
        return self.text
    