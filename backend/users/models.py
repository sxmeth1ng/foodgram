from django.contrib.auth.models import AbstractUser
from django.db import models

from users.utils import generate_avatar_path
from users.validators import validate_username


class CustomUser(AbstractUser):
    """Модель пользователя на основе базовой модели AbstractUser."""

    username = models.CharField(
        'Имя пользователя',
        unique=True,
        max_length=150,
        validators=[validate_username],
    )
    email = models.EmailField(
        'e-mail',
        unique=True,
        max_length=254,
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )
    subscriptions = models.ManyToManyField(
        'self',
        verbose_name='Подписки',
        related_name='subscribers',
        symmetrical=False,
        blank=True
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to=generate_avatar_path,
        null=True,
        blank=True,
    )
    favorite_recipes = models.ManyToManyField(
        'recipes.Recipe',
        related_name='favorite_recipes',
        blank=True,
    )
    shopping_cart = models.ManyToManyField(
        'recipes.Recipe',
        related_name='shopping_cart_recipes',
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
        return self.username[:30]
