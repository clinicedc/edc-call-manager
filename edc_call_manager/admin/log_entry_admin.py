from django.contrib import admin
from edc_model_admin.dashboard import ModelAdminSubjectDashboardMixin
from edc_model_admin.history import SimpleHistoryAdmin
from edc_model_admin.mixins import StackedInlineModelAdminMixin

from ..admin_site import edc_call_manager_admin
from ..forms import LogEntryForm
from ..models import LogEntry
from .modeladmin_mixins import LogEntryModelAdminMixin


@admin.register(LogEntry, site=edc_call_manager_admin)
class LogEntryAdmin(
    LogEntryModelAdminMixin, ModelAdminSubjectDashboardMixin, SimpleHistoryAdmin
):
    form = LogEntryForm


class LogEntryInlineAdmin(
    LogEntryModelAdminMixin, StackedInlineModelAdminMixin, admin.StackedInline
):
    form = LogEntryForm
    model = LogEntry
    extra = 0
