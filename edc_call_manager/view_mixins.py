from itertools import chain

from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.urls import reverse
from django.utils.decorators import method_decorator
from edc_dashboard.view_mixins import EdcViewMixin

from edc_utils import formatted_age
from edc_call_manager.constants import NO_CONTACT, INDIRECT_CONTACT, DIRECT_CONTACT
from edc_constants.constants import ALIVE, CLOSED, NO

from .caller_site import site_model_callers
from .forms import LogEntryForm


app_config = django_apps.get_app_config("edc_call_manager")
Call = django_apps.get_model(app_config.app_label, "call")
Log = django_apps.get_model(app_config.app_label, "log")
LogEntry = django_apps.get_model(app_config.app_label, "logentry")


class CallSubjectViewMixin(EdcViewMixin):

    template_name = "edc_call_manager/call_subject.html"
    form_class = LogEntryForm
    show_instructions = True
    instructions = "Complete the form as required."

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CallSubjectViewMixin, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse(
            "edc_call_manager_admin:{}_{}_changelist".format(
                *Call._meta.label_lower.split(".")
            )
        )

    def get_form_kwargs(self):
        kwargs = super(CallSubjectViewMixin, self).get_form_kwargs()
        kwargs["initial"].update({"log": self.log, "survival_status": ALIVE})
        return kwargs

    def get_object(self):
        return LogEntry.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject_identifier = self.log.call.subject_identifier
        call_status = self.log.call.get_call_status_display()
        if app_config.verbose_name not in context.get("project_name"):
            context.update(
                {
                    "project_name": context.get("project_name")
                    + ": "
                    + app_config.verbose_name
                }
            )
        context.update(
            instructions=self.instructions,
            show_instructions=self.show_instructions,
            caller_label=self.kwargs.get("caller_label"),
            contact_information=self.get_contact_information(),
            subject_identifier=subject_identifier,
            call_status=call_status,
            log_pk=str(self.kwargs.get("log_pk")),
            next_url=self.get_success_url(),
            label="call",
            **dict(
                chain.from_iterable(
                    d.items()
                    for d in (
                        self.demographics,
                        self.contact_history,
                        self.appointments,
                    )
                )
            ),
        )
        return context

    @property
    def log(self):
        return Log.objects.get(pk=self.kwargs.get("log_pk"))

    @property
    def model_caller(self):
        return site_model_callers.get_model_caller(self.kwargs.get("caller_label"))

    @property
    def demographics(self):
        dob = None
        first_name = self.log.call.first_name or ""
        gender = None
        last_name = None
        consent = self.model_caller.consent(self.log.call.subject_identifier)
        if consent:
            dob = consent.dob
            first_name = consent.first_name
            gender = consent.get_gender_display()
            last_name = consent.last_name
        else:
            subject = self.model_caller.subject(self.log.call.subject_identifier)
            if subject:
                dob = self.get_attr(subject, "dob")
                first_name = self.get_attr(subject, "first_name") or first_name
                gender = self.get_attr(subject, "gender")
                last_name = self.get_attr(subject, "last_name")
        name = "{} {}".format(first_name, last_name or "")
        name = None if name == " " else name
        return {
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "dob": dob,
            "age": formatted_age(dob),
        }

    @property
    def appointments(self):
        appointments = []
        appt = {}
        history = LogEntry.objects.filter(log=self.log).order_by("-call_datetime")
        for obj in history:
            try:
                appt = {
                    "appt_date": obj.appt_date.strftime("%Y-%m-%d"),
                    "appt_grading": obj.get_appt_grading_display(),
                }
            except AttributeError:
                pass
        appointments.append(appt)
        return {"appointments": appointments}

    @property
    def locator_model(self):
        return self.model_caller.locator_model

    @property
    def consent_model(self):
        return self.model_caller.consent_model

    @property
    def subject_model(self):
        return self.model_caller.subject_model

    def get_contact_information(self):
        try:
            contact_information = self.locator_model.objects.get(
                subject_identifier=self.log.call.subject_identifier
            ).to_dict()
        except self.locator_model.DoesNotExist:
            contact_information = None
        return contact_information

    @property
    def contact_history(self):
        history = LogEntry.objects.filter(log=self.log).order_by("-call_datetime")
        contact_history = {
            "attempts": history.filter(log=self.log).count(),
            "direct_contact": history.filter(
                log=self.log, contact_type=DIRECT_CONTACT
            ).count(),
            "indirect_contact": history.filter(
                log=self.log, contact_type=INDIRECT_CONTACT
            ).count(),
            "no_contact": history.filter(log=self.log, contact_type=NO_CONTACT).count(),
            "do_not_call": self.do_not_call(history),
            "call_closed": self.call_closed(history),
            "contact_history": history,
        }
        return contact_history

    def do_not_call(self, history):
        try:
            history.get(may_call=NO)
            do_not_call = True
        except MultipleObjectsReturned:
            do_not_call = True
        except ObjectDoesNotExist:
            do_not_call = False
        return do_not_call

    def call_closed(self, history):
        try:
            history.get(log__call__call_status=CLOSED)
            call_closed = True
        except MultipleObjectsReturned:
            call_closed = True
        except ObjectDoesNotExist:
            call_closed = False
        return call_closed

    def get_attr(self, obj, name):
        """Safely try to get the attr."""
        try:
            attr = getattr(obj, name)
        except AttributeError:
            attr = None
        return attr
