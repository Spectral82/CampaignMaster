from django.conf import settings
from django.core import signing
from django.core.mail import send_mail

SALT = "users.verify_email"


def generate_token(user) -> str:
    return signing.dumps({"user_id": user.pk}, salt=SALT)


def verify_token(token: str):
    try:
        data = signing.loads(token, salt=SALT, max_age=60 * 60 * 24)  # сутки
        return data["user_id"]
    except (signing.BadSignature, KeyError):
        return None


def send_verification_email(request, user):
    from django.urls import reverse

    link = request.build_absolute_uri(reverse("users:verify_email", args=[generate_token(user)]))
    send_mail(
        subject="Подтвердите email — CampaignMaster",
        message=f"Здравствуйте, {user.username}!\n\n"
                f"Подтвердите регистрацию по ссылке:\n{link}\n\n"
                f"Ссылка действует 24 часа.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )