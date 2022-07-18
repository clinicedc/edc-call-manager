from datetime import date

from django.apps import apps as django_apps
from django.db import models
from django.db.models import PROTECT
from django.utils import timezone
from django_crypto_fields.fields import EncryptedTextField, FirstnameField
from edc_constants.choices import ALIVE_DEAD_UNKNOWN, TIME_OF_DAY, TIME_OF_WEEK, YES_NO
from edc_constants.constants import ALIVE, CLOSED, DEAD, NO, YES
from edc_model.validators import date_is_future, datetime_not_future
from edc_model_fields.fields import OtherCharField
from edc_protocol.validators import datetime_not_before_study_start

from .choices import (
    APPT_GRADING,
    APPT_LOCATIONS,
    APPT_REASONS_UNWILLING,
    CALL_REASONS,
    CONTACT_TYPE,
    MAY_CALL,
)
from .constants import NEW_CALL, OPEN_CALL
from .managers import CallManager, LogEntryManager, LogManager

app_config = django_apps.get_app_config("edc_call_manager")


class CallModelMixin(models.Model):

    subject_identifier = models.CharField(max_length=50)

    label = models.CharField(max_length=50)

    scheduled = models.DateField(default=date.today)

    repeats = models.BooleanField(default=False)

    call_datetime = models.DateTimeField(
        null=True,
        editable=False,
        help_text="last call datetime updated by call log entry",
    )

    first_name = FirstnameField(verbose_name="First name", editable=False, null=True)

    initials = models.CharField(
        verbose_name="Initials", max_length=3, editable=False, null=True
    )

    consent_datetime = models.DateTimeField(
        verbose_name="Consent date and time",
        validators=[
            datetime_not_before_study_start,
            datetime_not_future,
        ],
        help_text="From Subject Consent.",
        null=True,
    )

    call_attempts = models.IntegerField(default=0)

    call_outcome = models.TextField(max_length=150, null=True)

    call_status = models.CharField(
        max_length=15,
        choices=((NEW_CALL, "New"), (OPEN_CALL, "Open"), (CLOSED, "Closed")),
        default=NEW_CALL,
    )

    auto_closed = models.BooleanField(
        default=False,
        editable=False,
        help_text="If True call status was changed to CLOSED by EDC.",
    )

    objects = CallManager()

    def natural_key(self):
        return self.subject_identifier, self.label, self.scheduled

    def __str__(self):
        return "{} {} ({}) {}".format(
            self.subject_identifier,
            self.first_name or "??",
            self.initials or "??",
            self.get_call_status_display(),
            " by EDC" if self.auto_closed else "",
        )

    class Meta:
        unique_together = (
            "subject_identifier",
            "label",
            "scheduled",
        )
        abstract = True


class LogModelMixin(models.Model):

    log_datetime = models.DateTimeField(editable=False, default=timezone.now)

    locator_information = EncryptedTextField(
        null=True,
        help_text="This information has been imported from the previous locator. You may update as required.",
    )

    contact_notes = EncryptedTextField(null=True, blank=True, help_text="")

    objects = LogManager()

    def natural_key(self):
        return (self.log_datetime,) + self.call.natural_key()

    natural_key.dependencies = ["{}.call".format(app_config.app_label)]

    def __str__(self):
        return str(self.call)

    class Meta:
        unique_together = (
            "log_datetime",
            "call",
        )
        abstract = True


class LogEntryModelMixin(models.Model):

    call_reason = models.CharField(
        verbose_name="Reason for this call",
        max_length=25,
        choices=CALL_REASONS,
    )

    call_datetime = models.DateTimeField(verbose_name="Date of this call")

    contact_type = models.CharField(
        max_length=15,
        choices=CONTACT_TYPE,
        help_text="If no contact made. STOP. Save form.",
    )

    survival_status = models.CharField(
        verbose_name="Survival status of the participant",
        max_length=10,
        choices=ALIVE_DEAD_UNKNOWN,
        default=ALIVE,
        null=True,
    )

    time_of_week = models.CharField(
        verbose_name="Time of week when participant will be available",
        max_length=25,
        choices=TIME_OF_WEEK,
        blank=True,
        null=True,
    )

    time_of_day = models.CharField(
        verbose_name="Time of day when participant will be available",
        max_length=25,
        choices=TIME_OF_DAY,
        blank=True,
        null=True,
    )

    appt = models.CharField(
        verbose_name="Is the participant willing to schedule an appointment",
        max_length=7,
        choices=YES_NO,
        null=True,
        blank=True,
    )

    appt_reason_unwilling = models.CharField(
        verbose_name="What is the reason the participant is unwilling to schedule an appointment",
        max_length=25,
        choices=APPT_REASONS_UNWILLING,
        null=True,
        blank=True,
    )

    appt_reason_unwilling_other = models.CharField(
        verbose_name="Other reason, please specify ...",
        max_length=50,
        null=True,
        blank=True,
    )

    appt_date = models.DateField(
        verbose_name="Appointment Date",
        validators=[date_is_future],
        null=True,
        blank=True,
        help_text="This can only come from the participant.",
    )

    appt_grading = models.CharField(
        verbose_name="Is this appointment...",
        max_length=25,
        choices=APPT_GRADING,
        null=True,
        blank=True,
    )

    appt_location = models.CharField(
        verbose_name="Appointment location",
        max_length=50,
        choices=APPT_LOCATIONS,
        null=True,
        blank=True,
    )

    appt_location_other = OtherCharField(
        verbose_name="Other location, please specify ...",
        max_length=50,
        null=True,
        blank=True,
    )

    delivered = models.BooleanField(default=False, editable=False)

    may_call = models.CharField(
        verbose_name="May we continue to contact the participant?",
        max_length=10,
        choices=MAY_CALL,
        default=YES,
        null=True,
        blank=True,
    )

    objects = LogEntryManager()

    @property
    def subject(self):
        """Override to return the FK attribute to the subject.

        expects any model instance with fields ['first_name', 'last_name', 'gender', 'dob'].

        For example: self.registered_subject.

        See also: CallSubjectViewMixin.get_context_data()"""
        return None

    def natural_key(self):
        return (self.call_datetime,) + self.log.natural_key()

    natural_key.dependencies = ["{}.log".format(app_config.app_label)]

    def save(self, *args, **kwargs):
        if self.survival_status == DEAD:
            self.may_call = NO
        super(LogEntryModelMixin, self).save(*args, **kwargs)

    @property
    def outcome(self):
        outcome = []
        if self.appt_date:
            outcome.append("Appt. scheduled")
        if self.survival_status in [ALIVE, DEAD]:
            outcome.append("Alive" if ALIVE else "Deceased")
        elif self.may_call == NO:
            outcome.append("Do not call")
        return outcome

    def log_entries(self):
        return self.__class__.objects.filter(log=self.log)

    class Meta:
        unique_together = ("call_datetime", "log")
        abstract = True
