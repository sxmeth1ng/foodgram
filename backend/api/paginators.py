from rest_framework.pagination import PageNumberPagination

from recipes.constants import PAGINATOR_SIZE


class BasePaginator(PageNumberPagination):
    """Пагинатор для пользователей и рецептов."""

    page_size_query_param = 'limit'
    page_size = PAGINATOR_SIZE
