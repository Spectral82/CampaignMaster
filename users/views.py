from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import RegisterForm
from .models import User
from .utils import send_verification_email, verify_token


class RegisterView(generic.CreateView):
    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:verify_notice")

    def form_valid(self, form):
        # деактивируем аккаунт ДО сохранения, а не после
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        try:
            send_verification_email(self.request, user)
            messages.success(self.request, "Письмо со ссылкой подтверждения отправлено на вашу почту.")
        except Exception as e:
            messages.warning(self.request, f"Аккаунт создан, но письмо не отправлено: {e}")
        return redirect(self.get_success_url())


class VerifyEmailView(generic.View):
    def get(self, request, token):
        user_id = verify_token(token)
        if user_id is None:
            messages.error(request, "Ссылка недействительна или устарела.")
            return redirect("users:register")
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            messages.error(request, "Пользователь не найден.")
            return redirect("users:register")
        user.is_verified = True
        user.is_active = True
        user.save(update_fields=["is_verified", "is_active"])
        send_welcome_email(user)
        login(request, user)
        messages.success(request, "Email подтверждён! Добро пожаловать.")
        return redirect("main:home")


def send_welcome_email(user):
    try:
        send_mail(
            subject="Добро пожаловать в CampaignMaster!",
            message=f"{user.username}, ваш email подтверждён. Регистрация завершена.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
    except Exception:
        pass  # письмо приветствия не блокирует вход


class VerifyEmailNoticeView(generic.TemplateView):
    template_name = "users/verify_email.html"


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"

    def form_valid(self, form):
        if not form.get_user().is_verified:
            messages.warning(self.request, "Подтвердите email по ссылке из письма.")
            return redirect("users:login")
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    pass


class UserListView(generic.ListView):
    model = User
    template_name = "mailings/manager_users.html"
    context_object_name = "users"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and (user.is_superuser or user.has_perm("users.can_block_users"))):
            messages.error(request, "Доступ только для менеджеров.")
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)


class BlockUserView(generic.View):
    def post(self, request, pk):
        if not (request.user.is_superuser or request.user.has_perm("users.can_block_users")):
            messages.error(request, "Доступ только для менеджеров.")
            return redirect("/")
        target = User.objects.filter(pk=pk).first()
        if target:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            state = "разблокирован" if target.is_active else "заблокирован"
            messages.success(request, f"Пользователь {target.email} {state}.")
        return redirect("users:list")


from django.shortcuts import render

# Create your views here.
