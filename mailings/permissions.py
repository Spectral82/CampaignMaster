from django.contrib.auth.mixins import UserPassesTestMixin


def is_manager(user):
    return user.is_superuser or user.has_perm("users.can_view_all_mailings")


def can_disable_mailing(user):
    """Право на отключение/включение рассылок — отдельное от просмотра."""
    return user.is_superuser or user.has_perm("users.can_disable_mailing")


class OwnerRequiredMixin(UserPassesTestMixin):
    """Для Update/Delete: управлять можно только своими объектами."""
    permission_denied_message = "Можно управлять только своими данными."

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.owner or self.request.user.is_superuser


class OwnerOrManagerMixin(UserPassesTestMixin):
    """Для Detail: владелец или менеджер (просмотр)."""
    permission_denied_message = "Нет доступа к этой записи."

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.owner or is_manager(self.request.user)


class ManagerRequiredMixin(UserPassesTestMixin):
    permission_denied_message = "Доступ только для менеджеров."

    def test_func(self):
        return is_manager(self.request.user)