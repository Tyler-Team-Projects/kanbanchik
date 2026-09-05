from typing import Any, Optional


class BaseDomainException(Exception):
    """Базовое доменное исключение."""
    status_code: int = 400
    detail: str = "Ошибка"
    headers: Optional[dict[str, Any]] = None

    def __init__(self, detail: Optional[str] = None, headers: Optional[dict[str, Any]] = None) -> None:
        if detail is not None:
            self.detail = detail
        if headers is not None:
            self.headers = headers
        super().__init__(self.detail)


# ============================================
# Ошибки уровня HTTP (4xx, 5xx)
# ============================================

class BadRequestException(BaseDomainException):
    """400 Bad Request."""
    status_code: int = 400


class UnauthorizedException(BaseDomainException):
    """401 Unauthorized."""
    status_code: int = 401


class ForbiddenException(BaseDomainException):
    """403 Forbidden."""
    status_code: int = 403


class NotFoundException(BaseDomainException):
    """404 Not Found."""
    status_code: int = 404


class ConflictException(BaseDomainException):
    """409 Conflict."""
    status_code: int = 409


class UnprocessableEntityException(BaseDomainException):
    """422 Unprocessable Entity."""
    status_code: int = 422


class InternalServerErrorException(BaseDomainException):
    """500 Internal Server Error."""
    status_code: int = 500


# ============================================
# Ошибки аутентификации и авторизации
# ============================================

class InvalidCredentialsException(UnauthorizedException):
    """Неверные учетные данные."""
    def __init__(self) -> None:
        super().__init__("Неверная почта, username или пароль")


class TokenExpiredException(UnauthorizedException):
    """Токен истек."""
    def __init__(self) -> None:
        super().__init__("Время жизни токена истекло")


class InvalidTokenException(UnauthorizedException):
    """Неверный токен."""
    def __init__(self) -> None:
        super().__init__("Неверный токен")


class RefreshTokenNotFoundException(UnauthorizedException):
    """Refresh-токен не найден."""
    def __init__(self) -> None:
        super().__init__("Токен обновления не найден или срок его действия истек")


class UserInactiveException(UnauthorizedException):
    """Пользователь не активен."""
    def __init__(self) -> None:
        super().__init__("Пользователь не активен")


class PermissionDeniedException(ForbiddenException):
    """Недостаточно прав."""
    def __init__(self, detail: str = "Недостаточно прав для выполнения операции") -> None:
        super().__init__(detail)


# ============================================
# Ошибки пользователей
# ============================================

class UserNotFoundException(NotFoundException):
    """Пользователь не найден."""
    def __init__(self, user_id: Optional[str] = None, username: Optional[str] = None) -> None:
        if user_id:
            super().__init__(f"Пользователь с ID '{user_id}' не найден")
        elif username:
            super().__init__(f"Пользователь с username '{username}' не найден")
        else:
            super().__init__("Пользователь не найден")


class UserEmailAlreadyExistsException(ConflictException):
    """Email уже занят."""
    def __init__(self, email: str) -> None:
        super().__init__(f"Пользователь с email '{email}' уже существует")


class UserUsernameAlreadyExistsException(ConflictException):
    """Username уже занят."""
    def __init__(self, username: str) -> None:
        super().__init__(f"Пользователь с username '{username}' уже существует")


class UserAlreadyExistsException(ConflictException):
    """Пользователь уже существует."""
    def __init__(self, email: str, username: str) -> None:
        super().__init__(f"Пользователь с email '{email}' или username '{username}' уже существует")


# ============================================
# Ошибки досок
# ============================================

class BoardNotFoundException(NotFoundException):
    """Доска не найдена."""
    def __init__(self, board_id: str) -> None:
        super().__init__(f"Доска с ID '{board_id}' не найдена")


class BoardAlreadyArchivedException(BadRequestException):
    """Доска уже в архиве."""
    def __init__(self) -> None:
        super().__init__("Доска уже в архиве")


class BoardNotArchivedException(BadRequestException):
    """Доска не в архиве."""
    def __init__(self) -> None:
        super().__init__("Доска не в архиве")


# ============================================
# Ошибки колонок (lists)
# ============================================

class ListNotFoundException(NotFoundException):
    """Колонка не найдена."""
    def __init__(self, list_id: str) -> None:
        super().__init__(f"Колонка с ID '{list_id}' не найдена")


class ListAlreadyArchivedException(BadRequestException):
    """Колонка уже в архиве."""
    def __init__(self) -> None:
        super().__init__("Колонка уже в архиве")


class ListNotArchivedException(BadRequestException):
    """Колонка не в архиве."""
    def __init__(self) -> None:
        super().__init__("Колонка не в архиве")


class ListConflictUpdateException(ConflictException):
    """Конфликт обновления колонки."""
    def __init__(self) -> None:
        super().__init__(
            "Конфликт обновления: запись была изменена другим пользователем. "
            "Пожалуйста, обновите страницу и попробуйте снова."
        )


# ============================================
# Ошибки рабочих пространств (workspaces)
# ============================================

class WorkspaceNotFoundException(NotFoundException):
    """Рабочее пространство не найдено."""
    def __init__(self, workspace_id: str) -> None:
        super().__init__(f"Рабочее пространство с ID '{workspace_id}' не найдено")


class WorkspaceAlreadyArchivedException(BadRequestException):
    """Рабочее пространство уже в архиве."""
    def __init__(self) -> None:
        super().__init__("Рабочее пространство уже в архиве")


class WorkspaceMemberNotFoundException(NotFoundException):
    """Участник рабочего пространства не найден."""
    def __init__(self, user_id: str) -> None:
        super().__init__(f"Участник с ID '{user_id}' не найден в рабочем пространстве")


class WorkspaceMemberAlreadyExistsException(ConflictException):
    """Участник уже состоит в рабочем пространстве."""
    def __init__(self) -> None:
        super().__init__("Пользователь уже состоит в рабочем пространстве")


class WorkspaceOwnerCannotBeRemovedException(BadRequestException):
    """Нельзя удалить владельца пространства."""
    def __init__(self) -> None:
        super().__init__("Нельзя удалить владельца пространства")


class WorkspaceNameAlreadyExistsException(ConflictException):
    """Workspace с таким именем уже существует."""
    def __init__(self, name: str) -> None:
        super().__init__(f"Рабочее пространство с именем '{name}' уже существует")