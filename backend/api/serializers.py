from django.core.validators import MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tag, User, Favorite, ShoppingCart
)
from users.models import Subscription


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор модели пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )


class UserViewSerializer(UserSerializer):
    """Сериализатор для получения данных о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки на просматриваемый профиль."""

        user_id = self.context.get('request').user.id
        return Subscription.objects.filter(
            author=obj.id, user=user_id
        ).exists()


class UserCreateSerializer(UserSerializer):
    """Сериализатор для регистрации нового пользователя."""

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('password',)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        """После регистрации в ответе не должен передаваться пароль."""

        representation = super().to_representation(instance)
        representation.pop('password', None)
        return representation


class AvatarSerializer(UserViewSerializer):
    """Сериализатор для добавления и удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta(UserViewSerializer.Meta):
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения краткой информации о рецепте.

    Будет использоваться при получении списка подписок пользователя, где по
    каждому пользователю будет возвращаться список их рецептов в коротком виде.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionSerializer(UserViewSerializer):
    """Сериализатор для списка подписок пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserViewSerializer.Meta):
        fields = UserViewSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        """Получение списка рецептов пользователя"""
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        try:
            if recipes_limit:
                recipes = obj.recipes.all()[:int(recipes_limit)]
            else:
                recipes = obj.recipes.all()
            return RecipeShortSerializer(recipes, many=True).data
        finally:
            pass

    def get_recipes_count(self, obj):
        """Получение количества рецептов пользователя."""
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientRecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор отображения ингридиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta():
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
            'name',
            'measurement_unit',
        )


class IngredientRecipeAddSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингридиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta():
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserViewSerializer(read_only=True)
    ingredients = IngredientRecipeViewSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta():
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user_id = self.context.get('request').user.id
        return Favorite.objects.filter(
            user=user_id,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user_id = self.context.get('request').user.id
        return ShoppingCart.objects.filter(
            user=user_id, recipe=obj.id
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецептов."""

    author = UserViewSerializer(read_only=True)
    image = Base64ImageField(required=True)
    ingredients = IngredientRecipeAddSerializer(many=True)
    cooking_time = serializers.IntegerField(validators=(MinValueValidator(1),))
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta():
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
        )
        read_only_fields = ('author',)

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Отсутствует изображение.'
            )
        return image

    def validate(self, data):
        if 'ingredients' in data and not data['ingredients']:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один ингредиент.'
            )

        if 'tags' in data and not data['tags']:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один тег.'
            )
        if 'tags' in data and data['tags']:
            if len(data['tags']) != len(set(data['tags'])):
                raise serializers.ValidationError(
                    'Не допускается указание одинаковых тегов.'
                )
        if 'ingredients' in data and data['ingredients']:
            ingredient_ids = [
                ingredient['id'] for ingredient in data['ingredients']
            ]
            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    'Не допускается повторение ингредиентов.'
                )

        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user, **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        required_fields = ('tags', 'ingredients')
        missing_fields = [field for field in required_fields if field not in
                          validated_data]
        if missing_fields:
            raise serializers.ValidationError(
                {field: 'Обязательное поле.' for field in missing_fields}
            )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance.tags.set(tags)
        self.create_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeViewSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

    class Meta():
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if not data['user'] or not data['recipe']:
            raise serializers.ValidationError(
                'Заполнены не все поля.')

    def to_representation(self, instance):
        return RecipeViewSerializer(instance, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины покупок."""
    author = serializers.SerializerMethodField()

    class Meta():
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if not data['user'] or not data['recipe']:
            raise serializers.ValidationError(
                'Заполнены не все поля.')

    def to_representation(self, instance):
        return RecipeViewSerializer(instance, context=self.context).data


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    def validate(self, attrs):
        user_id = attrs.get('user')
        author_id = attrs.get('author')
        if user_id == author_id:
            raise serializers.ValidationError('Нельзя подписаться на самого '
                                              'себя.')
        return attrs

    class Meta:
        model = Subscription
        fields = ('user', 'author')
