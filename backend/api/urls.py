from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (
    IngredientViewSet, RecipeViewSet,
    TagViewSet, UserViewSet, redirect_short_link,
)

app_name = 'api'

router = SimpleRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<str:short_code>/',
         redirect_short_link,
         name='redirect-short-link'),
]
