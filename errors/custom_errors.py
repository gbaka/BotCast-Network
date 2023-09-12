class CommandArgumentError(Exception):
    """
    Возникает в случае неправильных аргументов, которые
    передал пользователь.
    """
    def __init__(self, message):
        super().__init__(message)

        
class CommandExecutionError(Exception):
    """
    Возникает в случае если формально аргументы пользователя верны, но
    Telegram API не позволил выполнить команду.
    """
    def __init__(self, message):
        super().__init__(message)
