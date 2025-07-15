# edc-call-manager

Configure models to manage scheduling calls to subjects.

For example, contact all subjects to complete a revised consent, study closure, etc.

## Installation

    pip install git+https://github.com/botswana-harvard/edc-call-manager@develop#egg=edc_call_manager

add the app to INSTALLED_APPS

    INSTALLED_APPS = (
        ...,
        edc_call_manager.apps.AppConfig,
        my_app.apps.MyAppAppConfig,
        )


## ModelCaller

The `ModelCaller` schedules calls to subjects. The `ModelCaller` is configured to schedule a call when a special `start` model is created. It can also be configured to cancel a call when a special `stop` model is created. A `ModelCaller` can also be configured to schedule and cancel a sequence of calls.

The special models are actually just normal models registered with the `ModelCaller` as its `start` and `stop` models. But the special models need to know the `subject_identifier` of the subject either as a field attribute or property.

For example, we need to call expecting mothers weekly until they deliver. We declare a ModelCaller `AnteNatalFollowUpModelCaller`. Since we enroll mothers antenatally with the `AnteNatalEnrollment` model we can use this as the "start" model. Once the `AnteNatalEnrollment` model is completed, the `AnteNatalFollowUpModelCaller` schedules the first weekly call to the mother. For each week until the mother delivers, a new call is scheduled.

When the mother delivers we complete the `PostNatalEnrollment` model and this can be used as our "stop" model. When the `PostNatalEnrollment` model is completed, the `AnteNatalFollowUpModelCaller` closes any new or open calls it scheduled for the mother.

"Scheduling a call" just means creating a `Call` instance with `call_status` set to NEW. Each attempt to contact the subject is tracked in the `LogEntry` model. `LogEntry` is related to `Call` via `Log`. The structure is LogEntry <-- Log <-- Call. The first attempt to contact the subject sets `call_status` to OPEN. The first successful attempt to contact the subject sets `call_status` to CLOSED.

Here is an example `ModelCaller` start model:

	class AnteNatalEnrollment(models.Model):

	    subject_identifier = models.CharField(
	        max_length=25)

	    subject_date = models.DateField(
	        default=datetime.now())

	    class Meta:
	        app_label = 'my_app'

... and stop model:

	class PostNatalEnrollment(models.Model):

	    subject_identifier = models.CharField(
	        max_length=25)

	    subject_date = models.DateField(
	        default=datetime.now())

	    class Meta:
	        app_label = 'my_app'

The `AnteNatalFollowUpModelCaller` ModelCaller is declared as follows:

	from edc_call_manager.model_caller import ModelCaller, WEEKLY
	from edc_call_manager.decorators import register

	from .models import MaternalConsent, PostNatalEnrollment, Locator

	@register(AnteNatalEnrollment, PostNatalEnrollment)
	class AnteNatalFollowUpModelCaller(ModelCaller):
	    label = 'Antenatal-to-Postnatal'
	    consent_model = MaternalConsent
	    locator_model = Locator
	    interval = WEEKLY

Included in the declaration are `consent_model` and `locator_model`. ModelCaller uses these model classes to extract personal information on the subject to inform the research assistant making the follow-up calls. In almost all cases, the subject has been consented and locator information captured. Having the locator information is important as there may be restrictions on when and where the subject may be contacted, if at all. The consent and locator models are built using model mixins available in projects `edc_consent` and `edc_locator`. Personal information is always encrypted at rest in any EDC model (see modules `django_crypto_fields` and `edc.core.crypto_fields`).


## Expected Flow

* ICF, complete `Consent` Form
* Complete `Locator` Form
* Complete the `ModelCaller` scheduling form (in the example this is `AntenatalEnrollment`)
* Go to `Call` in Admin
* Tick a participant to call
* Select `Call Participant` action item and click Go
* Complete the `Log Entry` for this call attempt.
* If call is closed, next call is scheduled by the ModelCaller
* Complete the `ModelCaller` unscheduling form (in the example this is `PostnatalEnrollment`)
* `ModelCaller` closes any calls still NEW or OPEN for this participant and managed by this `ModelCaller`.

## Making a call and updating the `Log`

Calls are made via the Call changelist in Admin. A researcher pulls up the Log by ticking the call instance for the participant, selecting the `Call Participant` action item, and clikcing Go. The EDC will navigate to the Add/Change view of the Log and Log Entries.

## Calls that repeat on a specified interval

In the example above, the ModelCaller creates the next WEEKLY call once the current call is CLOSED. It will do so until the `unscheduling` model is complete (in this case the `PostnatalEnrollment` model). The event of filling in the `unscheduling` model closes any scheduled calls for this participant managed by this ModelCaller.

## Management command to update calls

TODO: a management command may be run daily to inspect calls relative to the repeat interval specified on the ModelCaller. If the window period to make the current call has passed, the current call will be closed and a new call scheduled.

## Appointment Caller

TODO: The `AppointmentCaller` schedules calls X-days before the appointment date and unschedules the call once the visit report is complete.



