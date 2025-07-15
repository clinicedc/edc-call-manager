from django.apps import apps as django_apps
from django.core.exceptions import MultipleObjectsReturned
from django.db import models

app_config = django_apps.get_app_config("edc_call_manager")


class CallLogLocatorMixin(models.Model):
    """A Locator model mixin that has the Locator model update the Log if changed."""

    def save(self, *args, **kwargs):
        self.update_call_log()
        super(CallLogLocatorMixin, self).save(*args, **kwargs)

    def get_call_log_model(self):
        """If using the edc_call_manager, return the Log model so it can be updated."""
        try:
            return django_apps.get_model(app_config.app_label, "log")
        except LookupError:
            return None

    def get_call_log_options(self):
        """If using the edc_call_manager, return the Log model filter options."""
        return dict(call__registered_subject=self.registered_subject)

    def update_call_log(self):
        """If using the edc_call_manager, update the Log model otherwise do nothing."""
        Log = self.get_call_log_model()
        if Log:
            try:
                log = Log.objects.get(**self.get_call_log_options())
                log.locator_information = self.to_string()
                log.save()
            except MultipleObjectsReturned:
                for log in Log.objects.filter(**self.get_call_log_options()):
                    log.locator_information = self.to_string()
                    log.save()
            except Log.DoesNotExist:
                pass

    class Meta:
        abstract = True
