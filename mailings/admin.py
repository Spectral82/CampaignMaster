from django.contrib import admin

from .models import Mailing, MailingAttempt, Message, Recipient

admin.site.site_header = "Админка CampaignMaster"


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "owner")
    search_fields = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "start_time", "end_time", "owner", "is_active")
    list_filter = ("status", "is_active")


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "status", "attempt_time", "server_response")
    list_filter = ("status",)