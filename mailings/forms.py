from django import forms
from django.utils import timezone

from .models import Mailing, Message, Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ("email", "full_name", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")
        widgets = {"body": forms.Textarea(attrs={"rows": 6})}


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ("start_time", "end_time", "message", "recipients")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipients"].widget = forms.CheckboxSelectMultiple
        fmt = ["%Y-%m-%dT%H:%M"]
        self.fields["start_time"].input_formats = fmt
        self.fields["end_time"].input_formats = fmt

    def clean_start_time(self):
        start = self.cleaned_data["start_time"]
        # при редактировании неизменённая дата в прошлом — не ошибка
        if self.instance.pk and self.instance.start_time == start:
            return start
        if start < timezone.localtime():
            raise forms.ValidationError("Время начала не может быть в прошлом.")
        return start

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError("Время начала должно быть раньше времени окончания.")
        return cleaned