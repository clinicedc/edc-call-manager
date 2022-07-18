from django.contrib import admin
from edc_model_admin import SimpleHistoryAdmin
from edc_model_admin.dashboard import ModelAdminSubjectDashboardMixin

from ..admin_site import edc_call_manager_admin
from ..models import Log
from .log_entry_admin import LogEntryInlineAdmin
from .modeladmin_mixins import LogModelAdminMixin


@admin.register(Log, site=edc_call_manager_admin)
class LogAdmin(LogModelAdminMixin, ModelAdminSubjectDashboardMixin, SimpleHistoryAdmin):
    inlines = [LogEntryInlineAdmin]
