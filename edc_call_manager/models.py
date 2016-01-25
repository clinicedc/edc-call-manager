from datetime import date

from django.db import models
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from edc_base.audit_trail import AuditTrail
from edc_base.encrypted_fields import EncryptedTextField, FirstnameField
from edc_base.model.fields import OtherCharField
from edc_base.model.models import BaseUuidModel
from edc_base.model.validators import datetime_not_future, datetime_not_before_study_start, date_is_future
from edc_constants.choices import YES_NO_UNKNOWN, TIME_OF_DAY, TIME_OF_WEEK, YES_NO, ALIVE_DEAD_UNKNOWN
from edc_constants.constants import YES, CLOSED, OPEN, NEW, DEAD, NO, ALIVE
from edc_registration.models import RegisteredSubject

from .choices import CONTACT_TYPE, APPT_GRADING, APPT_LOCATIONS
from .caller_site import site_model_callers


class Call(BaseUuidModel):

    registered_subject = models.ForeignKey(RegisteredSubject, null=True)

    subject_identifier = models.CharField(max_length=25)

    label = models.CharField(max_length=25)

    scheduled = models.DateField(
        default=date.today)

    repeats = models.BooleanField(
        default=False)

    last_called = models.DateTimeField(
        null=True,
        editable=False,
        help_text='last call datetime updated by call log entry')

    first_name = FirstnameField(
        verbose_name='First name',
        editable=False,
        null=True)

    initials = models.CharField(
        verbose_name='Initials',
        max_length=3,
        editable=False,
        null=True)

    consent_datetime = models.DateTimeField(
        verbose_name="Consent date and time",
        validators=[
            datetime_not_before_study_start,
            datetime_not_future, ],
        help_text="From Subject Consent.",
        null=True)

    call_attempts = models.IntegerField(
        default=0)

    call_outcome = models.TextField(
        max_length=150,
        null=True)

    call_status = models.CharField(
        max_length=15,
        choices=(
            (NEW, 'New'),
            (OPEN, 'Open'),
            (CLOSED, 'Closed')),
        default=NEW)

    auto_closed = models.BooleanField(
        default=False,
        editable=False,
        help_text='If True call status was changed to CLOSED by EDC.')

    history = AuditTrail()

    def __str__(self):
        return '{} {} [{}{}]'.format(
            self.subject_identifier,
            self.first_name or '??',
            self.initials or '??',
            self.call_status,
            ' by EDC' if self.auto_closed else '')

    class Meta:
        app_label = 'edc_call_manager'
        unique_together = ('subject_identifier', 'label', 'scheduled', )


class Log(BaseUuidModel):

    call = models.ForeignKey(Call)

    locator_information = EncryptedTextField(
        null=True,
        help_text='This information has been imported from the previous locator. You may update as required.')

    contact_notes = EncryptedTextField(
        null=True,
        blank=True,
        help_text='')

    history = AuditTrail()

    def __str__(self):
        return str(self.call)

    class Meta:
        app_label = 'edc_call_manager'


class LogEntry (BaseUuidModel):

    log = models.ForeignKey(Log)

    call_datetime = models.DateTimeField()

    invalid_numbers = models.CharField(
        verbose_name='Indicate any invalid numbers dialed from the locator information above?',
        max_length=50,
        validators=[RegexValidator(
            regex=r'^[0-9]{7,8}(,[0-9]{7,8})*$',
            message='Only enter contact numbers separated by commas. No spaces and no trailing comma.'), ],
        null=True,
        blank=True,
        help_text='Separate by comma (,).')

    contact_type = models.CharField(
        max_length=15,
        choices=CONTACT_TYPE,
        help_text='If no contact made. STOP. Save form.')

    survival_status = models.CharField(
        verbose_name='Survival status of the participant',
        max_length=10,
        choices=ALIVE_DEAD_UNKNOWN)

    time_of_week = models.CharField(
        verbose_name='Time of week when participant will be available',
        max_length=25,
        choices=TIME_OF_WEEK,
        blank=True,
        null=True)

    time_of_day = models.CharField(
        verbose_name='Time of day when participant will be available',
        max_length=25,
        choices=TIME_OF_DAY,
        blank=True,
        null=True)

    appt = models.CharField(
        verbose_name='Is the participant willing to schedule an appointment',
        max_length=7,
        choices=YES_NO_UNKNOWN,
        null=True,
        blank=True)

    appt_date = models.DateField(
        verbose_name="Appointment Date",
        validators=[date_is_future],
        null=True,
        blank=True,
        help_text="This can only come from the participant.")

    appt_grading = models.CharField(
        verbose_name='Is this appointment...',
        max_length=25,
        choices=APPT_GRADING,
        null=True,
        blank=True)

    appt_location = models.CharField(
        verbose_name='Appointment location',
        max_length=50,
        choices=APPT_LOCATIONS,
        null=True,
        blank=True)

    appt_location_other = OtherCharField(
        verbose_name='Appointment location',
        max_length=50,
        null=True,
        blank=True)

    delivered = models.NullBooleanField(
        default=False,
        editable=False)

    call_again = models.CharField(
        verbose_name='Call the participant again?',
        max_length=10,
        choices=YES_NO,
        default=YES)

    history = AuditTrail()

    def save(self, *args, **kwargs):
        if self.survival_status == DEAD:
            self.call_again = NO
        super(LogEntry, self).save(*args, **kwargs)

    @property
    def outcome(self):
        outcome = []
        if self.appt_date:
            outcome.append('Appt. scheduled')
        if self.survival_status in [ALIVE, DEAD]:
            outcome.append('Alive' if ALIVE else 'Deceased')
        if self.call_again == YES:
            outcome.append('Call again')
        elif self.call_again == NO:
            outcome.append('Do not call')
        return outcome

    def log_entries(self):
        return self.__class__.objects.filter(log=self.log)

    class Meta:
        app_label = 'edc_call_manager'


@receiver(post_save, weak=False, dispatch_uid='model_caller_on_post_save')
def model_caller_on_post_save(sender, instance, raw, created, using, update_fields, **kwargs):
    """A signal that acts on scheduling and unscheduling models."""
    if not raw and created:
        site_model_callers.schedule_calls(sender, instance)
        site_model_callers.unschedule_calls(sender, instance)


@receiver(post_save, weak=False, dispatch_uid='call_on_post_save')
def call_on_post_save(sender, instance, raw, created, using, update_fields, **kwargs):
    """A signal that acts on the Call model and schedules a new call if the current one is closed
    and configured to repeat on the model_caller."""
    if not raw and not created:
        try:
            if instance.call_status == CLOSED:
                site_model_callers.unschedule_calls(sender, instance)
                site_model_callers.schedule_next_call(instance)
        except AttributeError as e:
            if 'has no attribute \'call_status\'' not in str(e):
                raise AttributeError(e)


@receiver(post_save, weak=False, dispatch_uid='log_entry_on_post_save')
def log_entry_on_post_save(sender, instance, raw, created, using, **kwargs):
    """Updates call after a log entry ('call_status', 'call_attempts', 'call_outcome')."""
    if not raw:
        try:
            site_model_callers.update_call_from_log(instance.log.call, log_entry=instance)
        except AttributeError as e:
            if 'has no attribute \'log\'' not in str(e):
                raise AttributeError(e)
