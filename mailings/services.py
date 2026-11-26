from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


class MailingNotActiveError(Exception):
    pass


def send_mailing(mailing: Mailing) -> list[MailingAttempt]:
    """Отправляет письма всем получателям одной рассылки.

    Попытки создаются через bulk_create (batch).
    Бросает MailingNotActiveError, если окно отправки не активно.
    """
    if not mailing.is_active:
        raise MailingNotActiveError("Рассылка отключена менеджером.")
    if not mailing.is_running_now():
        raise MailingNotActiveError("Отправка разрешена только между началом и окончанием рассылки.")

    attempts = []
    for recipient in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts.append(MailingAttempt(
                mailing=mailing,
                status=MailingAttempt.STATUS_SUCCESS,
                server_response="Письмо отправлено",
            ))
        except Exception as e:
            attempts.append(MailingAttempt(
                mailing=mailing,
                status=MailingAttempt.STATUS_FAIL,
                server_response=str(e),
            ))

    MailingAttempt.objects.bulk_create(attempts)  # batch-создание попыток
    mailing.update_status()
    return attempts


def get_user_stats(user) -> dict:
    """Статистика по рассылкам пользователя (с кешированием)."""
    from django.core.cache import cache

    key = f"stats_user_{user.pk}"
    stats = cache.get(key)
    if stats is None:
        mailings = Mailing.objects.filter(owner=user)
        attempts = MailingAttempt.objects.filter(mailing__owner=user)
        stats = {
            "total_mailings": mailings.count(),
            "active_mailings": sum(1 for m in mailings if m.is_running_now()),
            "total_attempts": attempts.count(),
            "success_attempts": attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count(),
            "fail_attempts": attempts.filter(status=MailingAttempt.STATUS_FAIL).count(),
            "sent_messages": attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count(),
        }
        cache.set(key, stats, timeout=60)
    return stats