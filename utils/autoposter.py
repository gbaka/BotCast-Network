import asyncio
from datetime import datetime, timedelta
from random import randint
from pyrogram import errors, client, types
from database import models

class AutoPoster:
    # TODO: написать вложенный класс под config  (а мб лучше не переписывать)

    # тут post используюется в значении message
    def __init__(self) -> None:
        self._task = None
        self._client = None
        self.texts = None
        self.chats = None
        self.delay = None
        self.status = None

    def _init_status(self):
        self.status = {
            "has_error" : False,
            "delay" : self.delay,
            "chat_amount" : len(self.chats),
            "text_amount" : len(self.texts),
            "total_posts" : 0,
            "chats_info" : {}
        }
        for chat_obj in self.chats:
            chat_id = chat_obj.chat_id
            self.status["chats_info"][chat_id] = {"chat_title" : chat_obj.name, "post_amount" : 0}   

    def increment_post_count(self, chat_id): 
        self.status["chats_info"][chat_id]["post_amount"] += 1
        self.status["total_posts"] += 1

    def get_status(self):
        return self.status

    def is_active(self):
        return bool(self._task)

    def start(self, client: client.Client, chats: list[models.Chat], texts: list[models.Text], delay: timedelta):
        self._client = client
        self.chats = chats
        self.texts = texts
        self.delay = delay
        self._init_status()

        if not self._task or self._task.done():
            self._task = asyncio.ensure_future(self.autoposting())
            

    def stop(self):
        if self._task and not self._task.done():
            status = self.status 
            self._task.cancel()
            self._task = None
            self._client = None
            self.chats = None
            self.texts = None
            self.delay = None
            self.status = None
            return status
    
    async def autoposting(self):
        while True:  
            for chat_obj in self.chats:
                indx = randint(0, self.status["text_amount"] - 1)
                text_obj = self.texts[indx]
                text = text_obj.text
                chat_id = chat_obj.chat_id

                try:
                    await self._client.send_message(chat_id, text)
                    self.increment_post_count(chat_id)
                except Exception:
                    self.status["has_error"] = True
                
            await asyncio.sleep(self.delay.total_seconds()) 
        
AUTOPOSTER = AutoPoster()
