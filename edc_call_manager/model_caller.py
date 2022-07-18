from datetime import date, datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from django.core.exceptions import (
    ImproperlyConfigured,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
from django.utils.text import slugify
from edc_constants.constants import CLOSED, DEAD, NO, YES
from edc_utils import get_utcnow
from tqdm import tqdm

from .constants import DAILY, MONTHLY, NEW_CALL, OPEN_CALL, WEEKLY, YEARLY


class ModelCaller:
    """A class that manages scheduling and unscheduling of subject calls.

    This class gets registered to site_model_callers and the
    activity of it's Scheduling and Unscheduling models is inspected
    in signals.
    """

    consent_model = None
    consent_model_key_field = "subject_identifier"
    interval = WEEKLY
    label = None
    locator_model = "edc_locator.subjectlocator"
    repeat_times = 0
    subject_model = "edc_registration.registeredsubject"  # model with PII attrs. Default: RegisteredSubject
    subject_model_key_field = "subject_identifier"
    verbose_name = None
    call_model = "edc_call_manager.call"
    log_model = "edc_call_manager.log"
    log_entry_model = "edc_call_manager.logentry"
    # intervals = [DAILY, WEEKLY, MONTHLY, YEARLY]

    def __init__(self, start_model, stop_model):
        self.call_model_cls = django_apps.get_model(self.call_model)
        self.log_model_cls = django_apps.get_model(self.log_model)
        self.log_entry_model_cls = django_apps.get_model(self.log_entry_model)
        self.start_model = start_model
        self.start_model_cls = django_apps.get_model(self.start_model)
        self.stop_model_cls = None if not stop_model else django_apps.get_model(stop_model)
        self.consent_model_cls = (
            None if not self.consent_model else django_apps.get_model(self.consent_model)
        )
        self.locator_model_cls = django_apps.get_model(self.locator_model)
        self.subject_model_cls = django_apps.get_model(self.subject_model)
        if self.consent_model_cls:
            if not [
                fld.name
                for fld in self.consent_model_cls._meta.fields
                if fld.name in [self.consent_model_key_field]
            ]:
                raise ImproperlyConfigured(
                    f"ModelCaller model '{self.consent_model_cls._meta.label_lower}."
                    f"does not have field '{self.consent_model_key_field}'. "
                    f"See {self.__class__.__name__}.consent_model_fk."
                )
        self.label = slugify(self.label or self.__class__.__name__)
        # if self.interval and self.interval not in self.intervals:
        #     raise ValueError(
        #         "ModelCaller expected an 'interval' for a call scheduled to repeat. "
        #         f"Expected one of {', '.join(self.intervals)}. Got {self.interval}."
        #     )
        self.repeats = True if self.stop_model_cls and self.repeat_times > 0 else False

    @property
    def start_model_options(self) -> dict:
        """Override"""
        return {}

    def call_datetime(self, start_model_obj: Any) -> datetime:
        """Override"""
        return get_utcnow()

    def schedule_calls(self) -> int:
        """Creates a new call instance for each instance in the
        start model queryset.

        A new call is not created if one already exists.
        """
        new_calls = 0
        total = self.start_model_cls.objects.filter(**self.start_model_options).count()
        for start_model_obj in tqdm(
            self.start_model_cls.objects.filter(**self.start_model_options), total=total
        ):
            try:
                self.call_model_cls.objects.get(
                    subject_identifier=start_model_obj.subject_identifier,
                    label=self.label,
                    call_status__in=[NEW_CALL, OPEN_CALL],
                )
            except ObjectDoesNotExist:
                self.create_call_and_log(start_model_obj)
                new_calls += 1
        return new_calls

    def create_call_and_log(self, start_model_obj):
        """Creates a call model instance and the corresponding
        Log model instance.
        """
        if self.consent_model:
            options = self.pii(start_model_obj)
        else:
            options = self.pii(start_model_obj)
        call = self.call_model_cls.objects.create(
            scheduled=self.call_datetime(start_model_obj),
            label=self.label,
            repeats=self.repeats,
            **options,
        )
        self.log_model_cls.objects.create(
            call=call,
            locator_information=self.locator_to_str(start_model_obj.subject_identifier),
        )

    def close_and_create_next(self, subject_identifier: str) -> None:
        pass

    def close_all_calls(self, subject_identifier: str) -> None:
        """Sets call as closed for this subject identifier"""
        self.call_model_cls.objects.filter(
            subject_identifier=subject_identifier, label=self.label
        ).exclude(call_status=CLOSED).update(call_status=CLOSED, auto_closed=True)

    # def schedule_next_call(self, call, scheduled_date=None):
    #     """Schedules the next call if either scheduled_date is
    #     provided or can be calculated.
    #     """
    #     scheduled_date = scheduled_date or self.get_next_scheduled_date(call.call_datetime)
    #     if scheduled_date:
    #         self.create_call_and_log(call, scheduled=scheduled_date)

    def pii(self, instance) -> dict:
        """Returns personal details (PII) for this subject"""
        subject = self.subject(instance.subject_identifier)
        options = {
            "subject_identifier": subject.subject_identifier,
            "first_name": subject.first_name,
            "initials": subject.initials,
        }
        if self.consent_model_key_field not in options:
            try:
                value = getattr(instance, self.consent_model_key_field)
            except AttributeError:
                pass
            else:
                options.update({self.consent_model_key_field: value})
        return options

    def subject(self, subject_identifier):
        """Return an instance of the subject model"""

        return self.subject_model_cls.objects.get(
            **{self.subject_model_key_field: subject_identifier}
        )

    def consent(self, subject_identifier):
        """Return an instance of the consent model or None"""
        consent = None
        if self.consent_model_cls:
            try:
                # TODO: shouldn't this be filtered for schedule
                consent = self.consent_model_cls.objects.get(
                    subject_identifier=subject_identifier
                )
            except MultipleObjectsReturned:
                consent = self.consent_model_cls.consent.consent_for_period(
                    subject_identifier, get_utcnow()
                )
            except ObjectDoesNotExist as e:
                raise ValueError(
                    f"ModelCaller '{self.label}' is configured to require a consent "
                    f"for subject '{subject_identifier}'. Got '{e}'"
                )
        return consent

    def get_next_scheduled_date(self, reference_date) -> date:
        """Returns the next scheduled date or None based on the
        interval.
        """
        # TODO: This needs to be a bit more sophisticated to
        #  avoid holidays, weekends, etc.
        scheduled_date = None
        if self.interval == DAILY:
            scheduled_date = reference_date + relativedelta(days=+1)
        elif self.interval == WEEKLY:
            scheduled_date = reference_date + relativedelta(
                days=+1, weekday=reference_date.weekday()
            )
        elif self.interval == MONTHLY:
            scheduled_date = reference_date + relativedelta(
                months=+1, weekday=reference_date.weekday()
            )
        else:
            pass
        return scheduled_date

    def update_call_from_log(self, call, log_entry, commit=True) -> None:
        """Updates the call_model instance with information from the
        log entry for this subject and model caller.

        Only updates call if this is the most recent log_entry.
        """
        log_entries = self.log_entry_model_cls.objects.filter(log=log_entry.log).order_by(
            "-call_datetime"
        )
        if log_entry.pk == log_entries[0].pk:
            call = self.call_model_cls.objects.get(pk=call.pk)
            if call.call_status == CLOSED:
                raise ValidationError("Call is closed. Perhaps catch this in the form.")
            call.call_outcome = ". ".join(log_entry.outcome)
            call.call_datetime = log_entry.call_datetime
            call.call_attempts = log_entries.count()
            if log_entry.may_call == NO or log_entry.survival_status == DEAD:
                if log_entry.survival_status == DEAD:
                    call.call_outcome = "Deceased. " + (call.call_outcome or "")
                call.call_status = CLOSED
            else:
                call.call_status = OPEN_CALL
                if log_entry.appt == YES and log_entry.appt_date:
                    call.call_status = CLOSED
            call.modified = log_entry.modified
            call.user_modified = log_entry.user_modified
            if commit:
                call.save()

    def locator_to_str(self, subject_identifier: str) -> str:
        """Returns the locator instance as a formatted string"""
        try:
            locator = self.locator_model_cls.objects.get(subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            locator_as_str = "locator not found."
        else:
            locator_as_str = self.to_string(locator)
        return locator_as_str

    def to_string(self, obj):
        return ", ".join([str(v) for k, v in obj.__dict__.items() if not k.startswith("_")])
