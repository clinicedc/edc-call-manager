from django.contrib import admin
from edc_model_admin.dashboard import ModelAdminSubjectDashboardMixin
from edc_model_admin.history import SimpleHistoryAdmin

from ..admin_site import edc_call_manager_admin
from ..models import Call
from .modeladmin_mixins import CallModelAdminMixin


@admin.register(Call, site=edc_call_manager_admin)
class CallAdmin(
    CallModelAdminMixin,
    ModelAdminSubjectDashboardMixin,
    SimpleHistoryAdmin,
):
    pass
