from rest_framework.pagination import PageNumberPagination


class BasePaginator(PageNumberPagination):
    """Пагинатор для пользователей и рецептов."""

    page_size_query_param = 'limit'
    page_size = 10
