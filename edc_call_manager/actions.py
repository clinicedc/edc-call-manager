from django.apps import apps as django_apps
from django.contrib import messages
from django.contrib.messages.constants import WARNING
from django.http.response import HttpResponseRedirect
from django.urls import reverse


def call_participant(modeladmin, request, queryset):
    """
    Redirects to a new or existing Log.
    """
    app_config = django_apps.get_app_config("edc_call_manager")
    if queryset.count() == 1:
        call = queryset[0]
        log = django_apps.get_model(app_config.app_label, "Log").objects.get(call=call)
        change_url = ("{}?next={}&q={}").format(
            reverse(
                "edc_call_manager_admin:{}_{}_change".format(
                    *log._meta.label_lower.split(".")
                ),
                args=(log.pk,),
            ),
            "edc_call_manager_admin:{}_{}_changelist".format(
                *call._meta.label_lower.split(".")
            ),
            request.GET.get("q"),
        )
        return HttpResponseRedirect(change_url)
    else:
        messages.add_message(
            request, WARNING, "Please select only one subject to call at a time."
        )


call_participant.short_description = "Call participant"
