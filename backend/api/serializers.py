from django.core.validators import MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, User


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

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.subscribers.filter(id=request.user.id).exists()


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


class AvatarSerializer(UserSerializer):
    """Сериализатор для добавления и удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta(UserSerializer.Meta):
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Проверка правильности текущего пароля."""
        check_result = self.context['request'].user.check_password(value)
        if check_result:
            return value
        else:
            raise serializers.ValidationError('Проверьте правильность указания'
                                              ' текущего пароля.')


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


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для списка подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверка, одписан ли текущий пользователь на этого."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.subscribers.filter(id=user.id).exists()
        )

    def get_recipes(self, obj):
        """Получение списка рецептов пользователя"""
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
            return RecipeShortSerializer(recipes, many=True).data
        else:
            return RecipeShortSerializer(obj.recipes.all(), many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов пользователя."""
        return obj.recipes.count()


class RecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для рецептов."""

    class Meta:
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


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для ингридиентов в рецепте."""

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


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


class IngredientRecipeViewSerializer(IngredientRecipeSerializer):
    """Сериализатор отображения ингридиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta(IngredientRecipeSerializer.Meta):
        fields = IngredientRecipeSerializer.Meta.fields + (
            'name',
            'measurement_unit',
        )


class IngredientRecipeAddSerializer(IngredientRecipeSerializer):
    """Сериализатор добавления ингридиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(validators=(MinValueValidator(1),))


class RecipeViewSerializer(RecipeSerializer):
    """Сериализатор рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserViewSerializer(read_only=True)
    ingredients = IngredientRecipeViewSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + (
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.favorite_recipes.filter(id=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.shopping_cart.filter(id=obj.id).exists()
        )


class RecipeCreateUpdateSerializer(RecipeSerializer):
    """Сериализатор создания и обновления рецептов."""

    author = UserViewSerializer(read_only=True)
    image = Base64ImageField(required=True)
    ingredients = IngredientRecipeAddSerializer(many=True)
    cooking_time = serializers.IntegerField(validators=(MinValueValidator(1),))
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields
        read_only_fields = ('author',)

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Отсутствует изображение.'
            )
        return image

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один ингредиент.'
            )
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Не допускается повторение ингредиентов.'
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один тег.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Не допускается указание '
                                              'одинаковых тегов.')
        return tags

    def create_ingredients(self, recipe, ingredients):
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
