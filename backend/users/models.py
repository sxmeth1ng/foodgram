from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

from users.utils import generate_avatar_path
from recipes.constants import (
    USERNAME_LENGTH,
    MAX_USERNAME
)


class User(AbstractUser):
    """Модель пользователя на основе базовой модели AbstractUser."""

    email = models.EmailField(
        'e-mail',
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=USERNAME_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=USERNAME_LENGTH,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to=generate_avatar_path,
        null=True,
        blank=True,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:MAX_USERNAME]


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed_by',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (UniqueConstraint(
            fields=('user', 'author'),
            name='unique_subscription',
        ),
        )
        ordering = ('user',)

    def __str__(self):
        return f'{self.user} формил подписку на {self.author}'
