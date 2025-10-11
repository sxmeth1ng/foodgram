from django.conf import settings
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from hashids import Hashids
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from djoser import views as djoser_views

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import BasePaginator
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer, RecipeShortSerializer, TagSerializer,
    IngredientSerializer, FavoriteSerializer, ShoppingCartSerializer,
    CreateSubscriptionSerializer
)
from api.utils import export_shopping_cart
from recipes.models import Ingredient, Recipe, Tag, User


def redirect_view(request, short_code):
    """Перенаправление на рецепт по короткой ссылке."""

    hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=8)
    decoded_id = hashids.decode(short_code)

    if decoded_id:
        obj_id = decoded_id[0]
        recipe = get_object_or_404(Recipe, id=obj_id)
        return redirect(f'recipes/{recipe.id}')
    return redirect('/404/')


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = BasePaginator
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            return (AllowAny(),)
        elif self.action in [
            'create',
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        ]:
            return (IsAuthenticated(),)
        elif self.action in ['update', 'partial_update', 'destroy']:
            return (IsAuthorOrReadOnly(),)
        else:
            return super().get_permissions()

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    @action(methods=('POST'), detail=True, url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        favorite_recipe = FavoriteSerializer(data={
            'user': user.id,
            'recipe': recipe.id
        })
        favorite_recipe.save()
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        count_to_del, _ = user.favorite_recipes.filter(id=recipe.id).delete()
        if count_to_del == 0:
            raise ValidationError(f'Не удалось удалить рецепт из избранных. '
                                  f'Рецепт с id {recipe.id} не добавлен в '
                                  f'избранные.')
        user.favorite_recipes.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('POST'), detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        shopping_cart_serializer = ShoppingCartSerializer(data={
                'user': user.id,
                'recipe': recipe.id
            })
        shopping_cart_serializer.save()
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        count_to_del, _ = user.shopping_cart.filter(id=recipe.id).delete()
        if count_to_del == 0:
            raise ValidationError(f'Не удалось удалить рецепт из избранных. '
                                  f'Рецепт с id {recipe.id} не добавлен в '
                                  f'избранные.')
        user.shopping_cart.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        obj = get_object_or_404(Recipe, id=pk)
        salt = getattr(settings, 'HASHIDS_SALT')
        hashids = Hashids(salt=salt, min_length=8)
        short_code = hashids.encode(obj.id)
        short_url = request.build_absolute_uri(f'/s/{short_code}')

        return Response({'short-link': short_url}, status=status.HTTP_200_OK)

    @action(
        methods=('GET',),
        detail=False,
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        user = request.user
        cart_ingredients = (
            user.shopping_cart.prefetch_related(
                'recipe_ingredients__ingredient'
            )
            .values(
                'recipe_ingredients__ingredient__name',
                'recipe_ingredients__ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('recipe_ingredients__amount'))
        )
        if not cart_ingredients:
            return Response(
                {'detail': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        to_buy_list = [{
            'Ингредиент': item['recipe_ingredients__ingredient__name'],
            'Ед.изм': item['recipe_ingredients__ingredient__measurement_unit'],
            'Количество': item['total_amount']
        } for item in cart_ingredients]
        return FileResponse(
            export_shopping_cart(to_buy_list),
            as_attachment=True,
            filename=f'shopping_list_{request.user.username}'
        )


class TagViewSet(ModelViewSet):
    """Вьюсет для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get',)


class IngredientViewSet(ModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    http_method_names = ('get',)


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    pagination_class = BasePaginator
    lookup_field = 'id'
    search_fields = (
        'username',
        'email',
    )

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return (AllowAny(),)
        elif self.action in {
            'me',
            'set_password',
            'avatar',
            'subscriptions',
            'subscribe',
        }:
            return (IsAuthenticated(),)
        else:
            return super().get_permissions()

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    @action(
        methods=('GET',),
        detail=False,
        url_path='me',
    )
    def me(self, request):
        return super().me(self.get_serializer(request.user).data)

    @action(
        methods=('PUT'),
        detail=False,
        url_path='me/avatar',
    )
    def avatar(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def avatar_delete(self, request):
        request.user.avatar.delete()
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.all()
        paginated_subscriptions = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(
            paginated_subscriptions,
            many=True
        )
        return (Response(serializer.data) if not paginated_subscriptions else
                self.get_paginated_response(serializer.data))

    @action(
        methods=('POST', 'DELETE'),
        detail=True,
        url_path='subscribe',
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            create_subscription_serializer = CreateSubscriptionSerializer(
                data={'user': user.id, 'author': author.id}
            )
            create_subscription_serializer.is_valid(raise_exception=True)
            create_subscription_serializer.save()
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        count_to_del, _ = user.subscriptions.filter(id=author.id).delete()
        if count_to_del == 0:
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.subscriptions.remove(author)
        return Response(status=status.HTTP_204_NO_CONTENT)
