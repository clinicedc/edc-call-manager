from django import forms
from edc_constants.constants import CLOSED, OTHER, YES

from .admin_site import edc_call_manager_admin
from .models import LogEntry


class LogEntryForm(forms.ModelForm):

    hidden_fields = ["log", "survival_status"]
    use_modeladmin = False
    admin_site = edc_call_manager_admin

    def clean(self):
        cleaned_data = super(LogEntryForm, self).clean()
        log = cleaned_data.get("log")
        if cleaned_data.get("appt_location") == OTHER and not cleaned_data.get(
            "appt_location_other"
        ):
            raise forms.ValidationError(
                "You wrote the appointment location is OTHER, please specify below."
            )
        if cleaned_data.get("appt") == YES and not cleaned_data.get("appt_date"):
            raise forms.ValidationError(
                "You wrote the participant is willing to make an appointment. "
                "Please specify the appointment date."
            )
        if cleaned_data.get("appt") == YES and not cleaned_data.get("appt_grading"):
            raise forms.ValidationError(
                "You wrote the participant is willing to make an appointment. "
                "Please specify if this is a firm appointment date or not."
            )
        if cleaned_data.get("appt") == YES and not cleaned_data.get("appt_location"):
            raise forms.ValidationError(
                "You wrote the participant is willing to make an appointment. "
                "Please specify the appointment location."
            )
        if log.call.call_status == CLOSED:
            raise forms.ValidationError(
                "This call is closed. You may not add to or change the call log."
            )
        return cleaned_data

    class Meta:
        model = LogEntry
        fields = "__all__"
