class BaseCommandError(Exception):
    """
    Базовый класс для пользовательских исключений, связанных с командами.
    """
    def __init__(self, message="", title="", execution_status=""):
        super().__init__(message)
        self.title = title
        self.execution_status = execution_status

    def set_title(self, title: str):
        self.title = title

    def get_title(self):
        return self.title
    
    def get_status(self):
        return self.execution_status

    def __str__(self):
        message = self.args[0]
        if message=="":
            return self.title
        return f"{self.title}\n\n{message}"


class CommandArgumentError(BaseCommandError):
    """
    Возникает в случае неправильных аргументов, которые передал пользователь.
    """
    def __init__(self, message="", title="⚠️ **Проверьте правильность преданных аргументов.**"):
        super().__init__(message, title, "Ошибка: неверные аргументы")


class CommandExecutionError(BaseCommandError):
    """
    Возникает в случае если формально аргументы пользователя верны, но
    Telegram API не позволил выполнить команду.
    """
    def __init__(self, message="", title="⚠️ **Ошибка при выполнении команды.**"):
        super().__init__(message, title, "Ошибка: неверный запрос")

