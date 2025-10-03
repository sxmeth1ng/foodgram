from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Настройки для работы с пользователями в админке."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Регистрация модели подписок в админке."""

    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'author__username',
    )

    def get_queryset(self, request):
        queryset = Subscription.objects.select_related('user')
        return queryset
