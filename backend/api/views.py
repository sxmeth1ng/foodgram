from django.conf import settings
from django.db.models import Sum, Count
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
    IngredientSerializer, CreateSubscriptionSerializer,
    SubscriptionSerializer, RecipeCreateUpdateSerializer
)
from api.utils import export_shopping_cart
from recipes.models import (
    Ingredient, Recipe, Tag, User, RecipeIngredient, ShoppingCart, Favorite
)
from users.models import Subscription


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
        return RecipeCreateUpdateSerializer

    @action(methods=('POST',), detail=True, url_path='favorite')
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        favorite, created = Favorite.objects.get_or_create(
            user=user,
            recipe=recipe
        )

        if not created:
            raise ValidationError({'detail': 'Рецепт уже есть в избранных.'})

        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        user = request.user

        _ = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=user,
            recipe_id=pk
        ).delete()

        if deleted_count == 0:
            raise ValidationError({
                'detail': f'Рецепт с id {pk} не найден в избранных.'
            })

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('POST',), detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        cart_item, created = ShoppingCart.objects.get_or_create(
            user=user,
            recipe=recipe
        )

        if not created:
            raise ValidationError(
                {'detail': 'Рецепт уже есть в списке покупок.'}
            )

        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        user = request.user
        _ = get_object_or_404(Recipe, id=pk)

        deleted_count, _ = ShoppingCart.objects.filter(
            user=user,
            recipe_id=pk
        ).delete()

        if deleted_count == 0:
            raise ValidationError({
                'detail': f'Рецепт с id {pk} не найден в списке покупок.'
            })

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
        user_recipes = [item.recipe_id for item in
                        ShoppingCart.objects.filter(user=user)]
        to_buy = (
            RecipeIngredient.objects.filter(recipe__in=user_recipes)
            .values('ingredient')
            .annotate(amount=Sum('amount'))
        )
        to_buy_list = []
        for item in to_buy:
            ingredient = Ingredient.objects.get(pk=item['ingredient'])
            amount = item['amount']
            to_buy_list.append({
                'Ингредиент': ingredient.name,
                'Ед.изм': ingredient.measurement_unit,
                'Количество': amount
            })
        return FileResponse(
            export_shopping_cart(to_buy_list),
            as_attachment=True,
            filename='shopping_list_{}.xlsx'.format(user.username)
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

    @action(
        methods=('GET',),
        detail=False,
        url_path='me',
    )
    def me(self, request):
        return super().me(request)

    @action(
        methods=('PUT',),
        detail=False,
        url_path='me/avatar',
        serializer_class=AvatarSerializer
    )
    def avatar(self, request):
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(followed_by__user=user).annotate(
            recipes_count=Count('recipes')
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

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
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        count_to_del, _ = Subscription.objects.filter(
            user=user, author_id=id
        ).delete()
        if count_to_del == 0:
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
