from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import cache_control, cache_page

from mailings.models import Mailing, Recipient


def compute_home_stats() -> dict:
    return {
        "total_mailings": Mailing.objects.count(),
        "active_mailings": sum(1 for m in Mailing.objects.all() if m.is_running_now()),
        "unique_recipients": Recipient.objects.count(),
    }


@method_decorator(cache_page(60), name="get")
@method_decorator(cache_control(max_age=60, public=True), name="get")
class HomeView(generic.TemplateView):
    template_name = "main/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # передаём функцию, а не готовый словарь — иначе запросы идут мимо кеша
        context["stats"] = cache.get_or_set("home_stats", compute_home_stats, timeout=60)
        return context