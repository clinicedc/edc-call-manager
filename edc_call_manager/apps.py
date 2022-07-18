import sys

from django.apps import AppConfig as DjangoAppConfig
from django.apps import apps as django_apps


class AppConfig(DjangoAppConfig):
    name = "edc_call_manager"
    verbose_name = "Call Manager"
    app_label = "edc_call_manager"  # app_label for models Call, Log, LogEntry if not default
    namespace = "edc-call-manager"
    has_exportable_data = True
    include_in_administration_section = True

    def ready(self):
        from edc_call_manager.caller_site import site_model_callers

        sys.stdout.write("Loading {} ...\n".format(self.verbose_name))
        sys.stdout.write(" * call models are in app {}.\n".format(self.app_label))
        site_model_callers.autodiscover()
        sys.stdout.write(" Done loading {}.\n".format(self.verbose_name))

    @property
    def call_model(self):
        return django_apps.get_model(self.app_label, "call")

    @property
    def log_model(self):
        return django_apps.get_model(self.app_label, "log")

    @property
    def log_entry_model(self):
        return django_apps.get_model(self.app_label, "logentry")
