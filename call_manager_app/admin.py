from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.decorators import register

from simple_history.admin import SimpleHistoryAdmin

from edc_base.modeladmin_mixins import (
    ModelAdminFormInstructionsMixin,
    ModelAdminFormAutoNumberMixin,
)
from edc_call_manager.admin import (
    edc_call_manager_admin,
    ModelAdminCallMixin,
    ModelAdminLogMixin,
    ModelAdminLogEntryMixin,
)

from .models import (
    TestModel,
    TestStartModel,
    TestStopModel,
    Locator,
    Call,
    Log,
    LogEntry,
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
