from edc_constants.constants import CLINIC, DWTA, HOME, NO, OTHER, TELEPHONE, YES

from .constants import DIRECT_CONTACT, INDIRECT_CONTACT, NO_CONTACT

CONTACT_TYPE = (
    (DIRECT_CONTACT, "Direct contact with participant"),
    (INDIRECT_CONTACT, "Contact with person other than participant"),
    (NO_CONTACT, "No contact made"),
)

APPT_LOCATIONS = (
    (HOME, "At home"),
    ("work", "At work"),
    (TELEPHONE, "By telephone"),
    (CLINIC, "At clinic"),
    (OTHER, "Other location"),
)


APPT_GRADING = (
    ("firm", "Firm appointment"),
    ("weak", "Possible appointment"),
    ("guess", "Estimated by RA"),
)

MAY_CALL = (
    (YES, "Yes, we may continue to contact the participant."),
    (NO, "No, participant has asked NOT to be contacted again."),
)

CALL_REASONS = (
    ("schedule_appt", "Schedule an appointment"),
    ("reminder", "Remind participant of scheduled appointment"),
    ("missed_appt", "Follow-up with participant on missed appointment"),
)

APPT_REASONS_UNWILLING = (
    ("not_interested", "Not interested in participating"),
    ("busy", "Busy during the suggested times"),
    ("away", "Out of town during the suggested times"),
    ("unavailable", "Not available during the suggested times"),
    (DWTA, "Prefer not to say why I am unwilling."),
    (OTHER, "Other reason ..."),
)
