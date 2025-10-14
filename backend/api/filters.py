from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов."""

    is_favorited = filters.BooleanFilter(
        method='is_in_favorite',
        label='В избранном',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_list',
        label='В списке покупок',
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги',
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def is_in_favorite(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_favorite__user=user)
        if not value and user.is_authenticated:
            return queryset.exclude(in_favorite__user=user)
        if value:
            return queryset.none()
        return queryset

    def is_in_shopping_list(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        if not value and user.is_authenticated:
            return queryset.exclude(in_shopping_cart__user=user)
        if value:
            return queryset.none()
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
