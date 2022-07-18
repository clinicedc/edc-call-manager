import jsonpickle

from django.apps import apps as django_apps
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from edc_constants.constants import ALIVE
from edc_dashboard.view_mixins import EdcViewMixin
from edc_protocol.view_mixins import EdcProtocolViewMixin

from .caller_site import site_model_callers
from .view_mixins import CallSubjectViewMixin

app_config = django_apps.get_app_config("edc_call_manager")
Call = django_apps.get_model(app_config.app_label, "call")
Log = django_apps.get_model(app_config.app_label, "log")
LogEntry = django_apps.get_model(app_config.app_label, "logentry")


class HomeView(EdcViewMixin, EdcProtocolViewMixin, TemplateView):

    template_name = "edc_call_manager/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"model_callers": site_model_callers.model_callers.values()})
        if app_config.verbose_name not in context.get("project_name"):
            context.update(
                {
                    "project_name": context.get("project_name")
                    + ": "
                    + app_config.verbose_name
                }
            )
        context.update({"app_label": app_config.app_label})
        context.update({"context": jsonpickle.encode(context)})
        return context


class CallSubjectCreateView(CallSubjectViewMixin, EdcProtocolViewMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = "Add Call Log Entry"
        return context

    def form_valid(self, form):
        form.instance.log = self.log
        form.instance.survival_status = ALIVE
        return super(CallSubjectCreateView, self).form_valid(form)

    def form_invalid(self, form):
        return super(CallSubjectCreateView, self).form_invalid(form)


class CallSubjectUpdateView(CallSubjectViewMixin, EdcProtocolViewMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = "Change Call Log Entry"
        return context

    def form_valid(self, form):
        form.instance.log = self.log
        form.instance.survival_status = ALIVE
        return super(CallSubjectUpdateView, self).form_valid(form)


class CallSubjectDeleteView(CallSubjectViewMixin, EdcProtocolViewMixin, DeleteView):

    success_url = reverse_lazy("call-subject-delete")
