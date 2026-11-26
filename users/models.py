from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Аватар")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    country = models.CharField(max_length=100, blank=True, verbose_name="Страна")
    is_verified = models.BooleanField(default=False, verbose_name="Email подтверждён")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        permissions = (
            ("can_view_all_mailings", "Может просматривать все рассылки и клиентов"),
            ("can_block_users", "Может блокировать пользователей"),
            ("can_disable_mailing", "Может отключать рассылки"),
        )

    def __str__(self):
        return self.email