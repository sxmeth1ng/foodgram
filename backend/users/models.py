from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class CustomUser(AbstractUser):
    """Модель пользователя на основе базовой модели AbstractUser."""

    username = models.CharField(
        'Имя пользователя',
        unique=True,
        max_length=150,
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
    avatar = models.ImageField(
        'Аватар',
        upload_to=generate_avatar_path,
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
        return self.username


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        CustomUser,
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


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe',
            ),
        )

    def __str__(self):
        return (
            f'{self.recipe} в списке покупок у {self.user}'
        )
