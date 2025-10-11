from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from .constants import (
    MIN_VALUE,
    MAX_VALUE,
    NAME_MAX_LENGTH,
    MEASURE_UNIT_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    SMALL_FIELD_MAX_LENGTH
)

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField('Название', max_length=SMALL_FIELD_MAX_LENGTH)
    slug = models.SlugField('Слаг', max_length=SMALL_FIELD_MAX_LENGTH)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=MEASURE_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_couple'
            )
        ]

    def __str__(self):
        return (
            f'{self.name}, {self.measurement_unit}'
        )


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    name = models.CharField('Название', max_length=NAME_MAX_LENGTH)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(
                MAX_VALUE, message='Превышено максимально допустимое значение.'
            )
        ),
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:50]

    def added_to_favorite(self):
        return self.favorite_recipes.count()

    added_to_favorite.short_description = 'Добавлено в избранное'


class RecipeIngredient(models.Model):
    """Модель для связки ингредиентов с рецептами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
    )
    amount = models.PositiveIntegerField(
        'Количество', validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(
                MAX_VALUE,
                message='Превышено максимально допустимое колличество')
        )
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
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


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe',
            ),
        )

    def __str__(self):
        return f'{self.recipe} в избранном у  {self.user}'
