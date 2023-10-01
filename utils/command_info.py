import config


COMMAND_INFO = {

    # general #

    "general"  :   ("Все команды бота делятся на 6 секций: `history`, `messages`, `chats`, `texts`, `notes`, `users`.\n\n"
                    
                    "Узнать о командах определенной секции вы можете использовав следующий синтаксис:\n"
                    "`/help [section : str]`\n\n"
                    "О боте:\n"
                    "`/about`"),

    # sections #

    "texts"    :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления каталогом тектсов, тексты из каталога "
                    "текстов необходимы для осуществления автопостинга и планирования сообщений.\n\n"

                    "__**Команды**__:\n"
                    "`/texts [page : int = 1]`\n- вывод страницы каталога текстов с номером page.\n\n"
                    "`/texts add [text : str]`\n- добавление текста text в каталог текстов.\n\n"
                    "`/texts del [text_id : int]`\n- удаление текста с ID равным text_id из каталога текство.\n\n"
                    "`/texts show [text_id : int]`\n- вывод текста с ID равным text_id.\n\n"  
                    "`/texts clear`\n- очистка каталога текстов."),

    "history"  :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления историей команд, в историю команд "
                    " автоматически записываются все пользовательские запросы на исполнение той или иной команды.\n\n"

                    "__**Команды:**__\n"
                    "`/history [page : int = 1]`\n- выводит страницу истории команд с номером page.\n\n"
                    "`/history -s [page : int =1]`\n- выводит страницу истории команд с номером page в сокращенной форме.\n\n"
                    "`/history clear`\n- очищает историю команд."),

    "notes"    :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления каталогом заметок, в каталоге заметок "
                    "вы можете хранить наиболее частоиспользуемые вами команды.\n\n"

                    "__**Команды:**__\n"
                    "`/notes [page : int = 1]`\n- выводит страницу каталога заметок с номером page.\n\n"
                    "`/notes add [note : str]`\n- добавлять заметку в каталог заметок.\n\n"
                    "`/notes del [note_id : int]`\n- удаляет заметку с ID равным note_id из каталога заметок\n\n"
                    "`/notes setdescr [note_id : int] [description : str]`\n- изменяет описание заметки с ID равным note_id на description.\n\n"
                    "`/notes clear`\n- очищает каталог заметок."),

    "chats"    :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления каталогом чатов, чаты из каталога чатов "
                    "необходимы для осуществления автопостинга и планирования сообщений.\n\n"

                    "__**Команды:**__\n"
                    "`/chats [page : int = 1]`\n- выводит страницу каталога чатов с номером page.\n\n"
                    "`/chats add [chat_link : str | chat_id : int | -this]`\n- добавляет чат в базу используя ID чата или ссылку для вступления.\n\n" 
                    "`/chats join [chat_link : str | chat_id : int | -this]`\n- бот вступает в указанный чат, не добавляя его в базу.\n\n" 
                    "`/chats leave [chat_link : str | chat_id : int | -this]`\n- бот покидает указанный чат.\n\n" 
                    "`/chats del [chat_id : int | -this]`\n- удаляяет из каталога чатов чат с ID равным chat_id.\n\n"
                    "`/chats info [chat_link : str | chat_id : int | -this]`\n- выводит информацию о чате.\n\n"
                    "`/chats clear`\n- очищает каталог чатов."),

    "messages" :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления отложенными сообщениями и работой автопостера.\n\n"

                    "__**Команды:**__\n"
                    "`/messages`\n- выводит информацию о текущих отложенных сообщениях.\n\n"
                    "`/messages [chat_id : int | -this]`\n- выводит информацию о текущих отложенных сообщениях для чата с ID равным chat_id.\n\n"
                   f"`/messages schedule [chat_id : int | -all | -this] [text_id : int | -random] [messages_amount : int] [delay : int (min) = {config.DELAYED_MESSAGE_TIME_DIFFERENCE}] [init_delay : int (min) = {config.INITIAL_SEND_DELAY}]`\n- планирует отложенные сообщения.\n\n"
                    "`/messages undo [chat_id : int | -this]`\n- отменяет отложенные сообщения для указанного чата.\n\n"
                    "`/messages undo -all`\n- отменяет отложенные сообщения для всех чатов.\n\n"
                   f"`/messages autopost [chat_id : int | -all | -this] [text_id : int | -random] [delay : int (min) = {config.AUTOPOST_MESSAGE_TIME_DIFFERENCE}]`\n- запуск автопостера.\n\n"
                    "`/messages autopost status`\n- выводит текущую статистику по отправленным автопостером сообщениям.\n\n"
                    "`/messages autopost stop`\n- остановка автопостера."),

    "users"    :   ("__**Описание:**__\n"
                    "Команды данной секции используются для управления пользователями.\n\n"

                    "__**Команды:**__\n"
                   f"`/users move [source_chat_id : int | -this] [target_chat_id : int | -this] [user_count : int = {config.DEFAULT_USERS_TO_MOVE}| -max ({config.MAX_USERS_TO_MOVE})]`\n - добавляет user_count "
                    "пользователей из чата источника в целевой чат.\n\n"
                    "`/users info [username : str | user_id : int]`\n- выводит информацию о пользователе.")

}