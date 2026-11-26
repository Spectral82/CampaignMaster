from django.conf import settings
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="recipients", verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылок"

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="messages", verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "Создана"
    STATUS_RUNNING = "Запущена"
    STATUS_COMPLETED = "Завершена"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="mailings", verbose_name="Сообщение")
    recipients = models.ManyToManyField(Recipient, related_name="mailings", verbose_name="Получатели")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="mailings", verbose_name="Владелец",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        permissions = (("can_send_mailing", "Может отправлять рассылки"),)

    def update_status(self):
        """Динамический пересчёт статуса по текущему времени."""
        now = timezone.localtime()
        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_COMPLETED
        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

    def is_running_now(self):
        now = timezone.localtime()
        return self.start_time <= now <= self.end_time

    def __str__(self):
        return f"Рассылка #{self.pk} ({self.status})"


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "Успешно"
    STATUS_FAIL = "Не успешно"
    STATUS_CHOICES = [(STATUS_SUCCESS, "Успешно"), (STATUS_FAIL, "Не успешно")]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка")

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"

    def __str__(self):
        return f"{self.mailing} — {self.status} в {self.attempt_time:%d.%m.%Y %H:%M}"