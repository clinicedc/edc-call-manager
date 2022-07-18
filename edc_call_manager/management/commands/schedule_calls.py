from django.core.management.base import BaseCommand, CommandError
from django.db.models.signals import post_save
from django.dispatch import Signal

from edc_call_manager.caller_site import site_model_callers


class Command(BaseCommand):

    help = "Schedule calls for given model caller if not already scheduled"

    def add_arguments(self, parser):
        parser.add_argument("start_model", type=str, help="Model caller app_label.model_name")

    def handle(self, *args, **options):
        Signal.disconnect(
            post_save,
            dispatch_uid="edc_call_manager_model_caller_on_post_save",
        )
        try:
            model_caller = site_model_callers.get_model_caller(options["start_model"])
        except KeyError:
            raise CommandError(
                f"Model caller for start_model not found. Expected one of {site_model_callers._registry}. "
                f"Got {options['start_model']}."
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Found model_caller '{ model_caller.label}' with call model "
                f"'{model_caller.call_model_cls._meta.label_lower}'."
            )
        )
        new_calls = model_caller.schedule_calls()
        if new_calls > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully scheduled calls for {new_calls} "
                    f"{model_caller.start_model_cls._meta.verbose_name}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "No new calls scheduled. At least one call for each "
                    f"{model_caller.start_model_cls._meta.verbose_name} is already scheduled."
                )
            )
