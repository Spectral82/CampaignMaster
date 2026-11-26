from django.core.management.base import BaseCommand, CommandError

from mailings.models import Mailing, MailingAttempt
from mailings.services import MailingNotActiveError, send_mailing


class Command(BaseCommand):
    help = "Отправить рассылку: python manage.py send_mailing <id>"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int)

    def handle(self, *args, **options):
        mailing = Mailing.objects.filter(pk=options["mailing_id"]).first()
        if mailing is None:
            raise CommandError(f"Рассылка #{options['mailing_id']} не найдена.")
        try:
            attempts = send_mailing(mailing)
            ok = sum(1 for a in attempts if a.status == MailingAttempt.STATUS_SUCCESS)
            self.stdout.write(self.style.SUCCESS(f"Готово: успешно {ok}, неуспешно {len(attempts) - ok}"))
        except MailingNotActiveError as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))