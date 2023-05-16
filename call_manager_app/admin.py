from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.decorators import register
from edc_model_admin.history import SimpleHistoryAdmin
from edc_model_admin.mixins import (
    ModelAdminFormAutoNumberMixin,
    ModelAdminFormInstructionsMixin,
)

from edc_call_manager.admin import (
    ModelAdminCallMixin,
    ModelAdminLogEntryMixin,
    ModelAdminLogMixin,
    edc_call_manager_admin,
)

from .models import (
    Call,
    Locator,
    Log,
    LogEntry,
    TestModel,
    TestStartModel,
    TestStopModel,
)

app_config = django_apps.get_app_config("edc_call_manager")


@register(TestModel)
class TestModelAdmin(ModelAdmin):
    pass


@register(TestStartModel)
class TestStartModelAdmin(ModelAdmin):
    pass


@register(TestStopModel)
class TestStopModelAdmin(ModelAdmin):
    pass


@register(Locator)
class LocatorAdmin(ModelAdmin):
    pass


class BaseModelAdmin(ModelAdminFormInstructionsMixin, ModelAdminFormAutoNumberMixin):
    list_per_page = 10
    date_hierarchy = "modified"
    empty_value_display = "-"


if app_config.app_label == "edc_call_manager_example":

    @admin.register(Call, site=edc_call_manager_admin)
    class CallAdmin(BaseModelAdmin, ModelAdminCallMixin, SimpleHistoryAdmin):
        pass

    @admin.register(Log, site=edc_call_manager_admin)
    class LogAdmin(BaseModelAdmin, ModelAdminLogMixin, SimpleHistoryAdmin):
        pass

    @admin.register(LogEntry, site=edc_call_manager_admin)
    class LogEntryAdmin(BaseModelAdmin, ModelAdminLogEntryMixin, SimpleHistoryAdmin):
        pass
