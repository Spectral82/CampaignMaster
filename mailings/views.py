from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from . import services
from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, MailingAttempt, Message, Recipient
from .permissions import OwnerOrManagerMixin, OwnerRequiredMixin, can_disable_mailing, is_manager


class RecipientListView(LoginRequiredMixin, generic.ListView):
    model = Recipient
    template_name = "mailings/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        if is_manager(self.request.user):
            return Recipient.objects.all()
        return Recipient.objects.filter(owner=self.request.user)


class RecipientDetailView(LoginRequiredMixin, OwnerOrManagerMixin, generic.DetailView):
    model = Recipient
    template_name = "mailings/recipient_detail.html"


class RecipientCreateView(LoginRequiredMixin, generic.CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("mailings:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Получатель добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, generic.UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("mailings:recipient_list")


class RecipientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, generic.DeleteView):
    model = Recipient
    template_name = "mailings/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailings:recipient_list")


class MessageListView(LoginRequiredMixin, generic.ListView):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "messages_list"

    def get_queryset(self):
        if is_manager(self.request.user):
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageDetailView(LoginRequiredMixin, OwnerOrManagerMixin, generic.DetailView):
    model = Message
    template_name = "mailings/message_detail.html"


class MessageCreateView(LoginRequiredMixin, generic.CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, generic.UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, generic.DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("mailings:message_list")


class MailingListView(LoginRequiredMixin, generic.ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        qs = Mailing.objects.select_related("message").prefetch_related("recipients")
        if is_manager(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class MailingDetailView(LoginRequiredMixin, OwnerOrManagerMixin, generic.DetailView):
    model = Mailing
    template_name = "mailings/mailing_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # динамический пересчёт статуса
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attempts"] = self.object.attempts.order_by("-attempt_time")[:20]
        return context


class MailingCreateView(LoginRequiredMixin, generic.CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.status = Mailing.STATUS_CREATED
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, generic.UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, generic.DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")


@login_required
def send_mailing_view(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if mailing.owner != request.user and not is_manager(request.user):
        messages.error(request, "Нет доступа.")
        return redirect("mailings:mailing_list")
    try:
        attempts = services.send_mailing(mailing)
        ok = sum(1 for a in attempts if a.status == MailingAttempt.STATUS_SUCCESS)
        messages.success(request, f"Отправка завершена: успешно {ok}, неуспешно {len(attempts) - ok}.")
    except services.MailingNotActiveError as e:
        messages.error(request, str(e))
    return redirect("mailings:mailing_detail", pk=pk)


@login_required
def disable_mailing_view(request, pk):
    """Отключение/включение рассылки — только по праву can_disable_mailing."""
    if not can_disable_mailing(request.user):
        messages.error(request, "У вас нет права отключать рассылки.")
        return redirect("/")
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.is_active = not mailing.is_active
    mailing.save(update_fields=["is_active"])
    state = "отключена" if not mailing.is_active else "включена"
    messages.success(request, f"Рассылка #{mailing.pk} {state}.")
    return redirect("mailings:mailing_detail", pk=pk)


class AttemptListView(LoginRequiredMixin, generic.ListView):
    model = MailingAttempt
    template_name = "mailings/attempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        qs = MailingAttempt.objects.select_related("mailing")
        if is_manager(self.request.user):
            return qs
        return qs.filter(mailing__owner=self.request.user)


class StatsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "mailings/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = services.get_user_stats(self.request.user)
        return context