import re

from django.core.exceptions import ValidationError


def validate_username(value: str) -> str:
    """Валидация для поля username."""
    if value == 'me':
        raise ValidationError(
            'Использование имени пользователя "me" запрещено.'
        )
    pattern = r'^[\w.@+-]+\Z'
    if not re.match(pattern, value):
        raise ValidationError(
            'Имя пользователя может содержать только буквы, цифры и символы '
            '@/./+/-/_'
        )
    return value
