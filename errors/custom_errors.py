class BaseCommandError(Exception):
    """
    Базовый класс для пользовательских исключений, связанных с командами.
    """
    def __init__(self, message="", title=""):
        super().__init__(message)
        self.title = title

    def set_title(self, title: str):
        self.title = title

    def get_title(self):
        return self.title

    def __str__(self):
        return f"{self.title}\n\n{self.args[0]}"


class CommandArgumentError(BaseCommandError):
    """
    Возникает в случае неправильных аргументов, которые передал пользователь.
    """
    def __init__(self, message=""):
        super().__init__(message, "⚠️ **Проверьте правильность преданных аргументов.**")


class CommandExecutionError(BaseCommandError):
    """
    Возникает в случае если формально аргументы пользователя верны, но
    Telegram API не позволил выполнить команду.
    """
    def __init__(self, message=""):
        super().__init__(message, "⚠️ **Ошибка при выполнении команды.**")

