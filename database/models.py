# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from utils import helpers
import datetime

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
    # date = Column(String)
    date = Column(DateTime)
    status = Column(String)

    def __str__(self):
        return (f"__Команда:__  `{self.command}`\n" +
                f"__Аргументы:__  `{helpers.truncate_string(self.command_arguments, 16)}`\n" +
                f"__Дата:__  {self.date.strftime('%d.%m.%Y %H:%M:%S')}\n" +
                f"__Имя пользователя:__  {helpers.truncate_string(self.user_name, 12)}\n" +
                f"__ID пользователя:__  {self.user_id}\n" +
                f"__Статус:__  {self.status}")
    


class Text(Base):
    __tablename__ = 'texts'

    text_id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)

    def __str__(self):
        return (f"__ID текста:__  {self.text_id}\n" + 
                f"__Текст:__\n\"{self.text}")
    

class Chat(Base):
    __tablename__ = 'chats'

    name = Column(String)
    chat_id = Column(Integer, primary_key=True) 
    participant_count=Column(Integer)
    date_added = Column(DateTime)

    def to_tuple(self):
        return (self.name, self.chat_id, self.participant_count, self.date_added)

    def __str__(self):
        return (f"__Название:__  {self.name}\n" +
                f"__ID чата:__  `{self.chat_id}`\n" +
                f"__Кол-во участников:__  {self.participant_count}\n" +
                f"__Дата добавления:__  {self.date_added.strftime('%d.%m.%Y %H:%M:%S')}")

    