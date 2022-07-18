import json
from datetime import date, timedelta

from django.apps import apps as django_apps
from django.core import serializers
from django.test.testcases import TestCase
from edc_constants.constants import ALIVE, CLOSED, DEAD, NO, YES
from edc_registration.models import RegisteredSubject
from edc_utils import get_utcnow

from call_manager_app.models import Locator, TestModel, TestStartModel, TestStopModel
from edc_call_manager.caller_site import AlreadyRegistered, site_model_callers
from edc_call_manager.constants import NEW_CALL, OPEN_CALL
from edc_call_manager.model_caller import WEEKLY, ModelCaller

app_config = django_apps.get_app_config("edc_call_manager")
Call = django_apps.get_model(app_config.app_label, "call")
Log = django_apps.get_model(app_config.app_label, "log")
LogEntry = django_apps.get_model(app_config.app_label, "logentry")


class TestModelCaller(ModelCaller):
    label = "TestModelCaller"
    app_label = "edc_call_manager_example"
    locator_model = Locator
    subject_model = RegisteredSubject


class RepeatingTestModelCaller(ModelCaller):
    label = "RepeatingTestModelCaller"
    app_label = "edc_call_manager_example"
    locator_model = Locator
    subject_model = RegisteredSubject
    interval = WEEKLY


class LocatorTestModelCaller(ModelCaller):
    label = "LocatorTestModelCaller"
    app_label = "edc_call_manager_example"
    interval = WEEKLY
    locator_model = Locator
    subject_model = RegisteredSubject


class TestCallManager(TestCase):
    def test_model_factory(self):
        return TestModel.objects.create(subject_identifier=self.subject_identifier)

    def test_start_model_factory(self):
        return TestStartModel.objects.create(subject_identifier=self.subject_identifier)

    def test_stop_model_factory(self):
        return TestStopModel.objects.create(subject_identifier=self.subject_identifier)

    def setUp(self):
        site_model_callers.reset_registry()
        site_model_callers.register(TestModelCaller, TestModel, TestStopModel, verbose=False)
        site_model_callers.register(
            RepeatingTestModelCaller, TestStartModel, TestStopModel, verbose=False
        )
        self.subject_identifier = "1111111"
        self.registered_subject = RegisteredSubject.objects.create(
            subject_identifier="1111111"
        )

    def test_register(self):
        self.assertIn(TestModel, site_model_callers.start_models)
        self.assertIn(TestStartModel, site_model_callers.start_models)

    def test_register_duplicate(self):
        class TestModelCaller2(ModelCaller):
            pass

        self.assertRaises(
            AlreadyRegistered,
            site_model_callers.register,
            TestModelCaller2,
            TestModel,
            TestStopModel,
        )

    def test_create_registered_model(self):
        TestModel.objects.create(subject_identifier=self.subject_identifier)
        self.assertEqual(
            Call.objects.filter(subject_identifier=self.subject_identifier).count(), 1
        )

    def test_call_defaults(self):
        self.test_model_factory()
        call = Call.objects.get(subject_identifier=self.subject_identifier)
        self.assertEqual(call.label, "testmodelcaller")
        self.assertFalse(call.repeats)

    def test_repeating_caller_defaults(self):
        self.test_start_model_factory()
        call = Call.objects.get(subject_identifier=self.subject_identifier)
        self.assertEqual(call.label, "RepeatingTestModelCaller".lower())
        self.assertTrue(call.repeats)

    def test_unscheduling_ignores_if_no_scheduled(self):
        self.test_stop_model_factory()
        self.assertRaises(
            Call.DoesNotExist,
            Call.objects.get,
            subject_identifier=self.subject_identifier,
        )

    def test_unscheduling_closes_if_scheduled(self):
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=self.subject_identifier,
                label="RepeatingTestModelCaller".lower(),
                call_status=NEW_CALL,
            ).count(),
            0,
        )
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=self.subject_identifier,
                label="RepeatingTestModelCaller".lower(),
                call_status=CLOSED,
            ).count(),
            0,
        )
        self.test_start_model_factory()
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=self.subject_identifier,
                label="RepeatingTestModelCaller".lower(),
                call_status=NEW_CALL,
            ).count(),
            1,
        )
        self.test_stop_model_factory()
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=self.subject_identifier,
                label="RepeatingTestModelCaller".lower(),
                call_status=CLOSED,
            ).count(),
            1,
        )

    def test_locator_not_found_for_log(self):
        site_model_callers.reset_registry()
        site_model_callers.register(LocatorTestModelCaller, TestStartModel, verbose=False)
        self.test_start_model_factory()
        call = Call.objects.get(
            subject_identifier=self.subject_identifier, call_status=NEW_CALL
        )
        log = Log.objects.get(call=call)
        self.assertEqual(log.locator_information, "locator not found.")

    def test_locator_as_string_for_log(self):
        site_model_callers.reset_registry()
        site_model_callers.register(LocatorTestModelCaller, TestStartModel, verbose=False)
        locator = Locator.objects.create(
            subject_identifier=self.subject_identifier,
            home_visit_permission=YES,
            physical_address="Near General Dealer with black steel gate",
            may_follow_up=YES,
            subject_cell="723333333",
            may_call_work=NO,
            may_contact_someone=NO,
        )
        self.test_start_model_factory()
        call = Call.objects.get(
            subject_identifier=self.subject_identifier, call_status=NEW_CALL
        )
        log = Log.objects.get(call=call)
        self.assertEqual(log.locator_information, locator.to_string())
        self.assertIn("723333333", log.locator_information)

    def test_log_entry_outcome_call_again(self):
        self.test_start_model_factory()
        call = Call.objects.get(
            subject_identifier=self.subject_identifier, call_status=NEW_CALL
        )
        call_pk = call.pk
        log = Log.objects.get(call=call)
        LogEntry.objects.create(
            log=log,
            call_datetime=get_utcnow(),
            contact_type="direct",
            survival_status=ALIVE,
        )
        call = Call.objects.get(pk=call_pk)
        self.assertIn("Alive", call.call_outcome)

    def test_log_entry_outcome_deceased(self):
        self.test_start_model_factory()
        call = Call.objects.get(
            subject_identifier=self.subject_identifier, call_status=NEW_CALL
        )
        call_pk = call.pk
        log = Log.objects.get(call=call)
        LogEntry.objects.create(
            log=log,
            call_datetime=get_utcnow(),
            contact_type="indirect",
            survival_status=DEAD,
        )
        call = Call.objects.get(pk=call_pk)
        self.assertEqual(call.call_status, CLOSED)
        self.assertIn("Deceased", call.call_outcome)

    def test_call_attempts(self):
        subject_identifier = self.subject_identifier
        self.test_start_model_factory()
        call = Call.objects.get(subject_identifier=subject_identifier, call_status=NEW_CALL)
        call_pk = call.pk
        log = Log.objects.get(call=call)
        LogEntry.objects.create(
            log=log,
            call_datetime=get_utcnow(),
            contact_type="indirect",
            survival_status=ALIVE,
        )
        call = Call.objects.get(pk=call_pk)
        self.assertEqual(call.call_attempts, 1)
        self.assertEqual(call.call_status, OPEN_CALL)
        LogEntry.objects.create(
            log=log,
            call_datetime=get_utcnow(),
            contact_type="direct",
            survival_status=ALIVE,
            appt=YES,
            appt_date=date.today() + timedelta(5),
        )
        call = Call.objects.get(pk=call_pk)
        self.assertEqual(call.call_attempts, 2)
        self.assertEqual(call.call_status, CLOSED)
        # created a new call after closing the previous
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=subject_identifier, label=call.label
            ).count(),
            2,
        )

    def test_schedule_next_call(self):
        subject_identifier = self.subject_identifier
        self.test_start_model_factory()
        call = Call.objects.get(subject_identifier=subject_identifier, call_status=NEW_CALL)
        call_pk = call.pk
        call_label = call.label
        log = Log.objects.get(call=call)
        LogEntry.objects.create(
            log=log,
            call_datetime=get_utcnow(),
            contact_type="indirect",
            survival_status=ALIVE,
            appt=YES,
            appt_date=date.today() + timedelta(days=5),
        )
        call = Call.objects.get(pk=call_pk)
        self.assertEqual(call.call_status, CLOSED)
        self.assertEqual(
            Call.objects.filter(
                subject_identifier=subject_identifier,
                label=call_label,
                call_status=NEW_CALL,
            )
            .exclude(pk=call_pk)
            .count(),
            1,
        )
        scheduled = (
            Call.objects.filter(
                subject_identifier=subject_identifier,
                label=call_label,
                call_status=NEW_CALL,
            )
            .exclude(pk=call_pk)[0]
            .scheduled
        )
        self.assertGreater(scheduled, call.scheduled)

    def test_call_serialize(self):
        self.test_model_factory()
        call = Call.objects.get(subject_identifier=self.subject_identifier)
        json_object = serializers.serialize(
            "json", [call], use_natural_foreign_keys=True, use_natural_primary_keys=True
        )
        self.assertTrue(json.loads(json_object))

    def test_log_serialize(self):
        self.test_model_factory()
        call = Call.objects.get(subject_identifier=self.subject_identifier)
        log = Log.objects.get(call=call)
        json_object = serializers.serialize(
            "json", [log], use_natural_foreign_keys=True, use_natural_primary_keys=True
        )
        self.assertTrue(json.loads(json_object))
        obj = json.loads(json_object)
        self.assertEqual(
            obj[0]["fields"]["call"],
            [
                self.subject_identifier,
                TestModelCaller.label.lower(),
                date.today().strftime("%Y-%m-%d"),
            ],
        )

    def test_logentry_serialize(self):
        self.test_model_factory()
        call = Call.objects.get(subject_identifier=self.subject_identifier)
        log = Log.objects.get(call=call)
        now = get_utcnow()
        today = date.today()
        log_entry = LogEntry.objects.create(
            log=log,
            call_datetime=now,
            contact_type="indirect",
            survival_status=ALIVE,
            appt=YES,
            appt_date=today + timedelta(days=5),
        )
        json_object = serializers.serialize(
            "json",
            [log_entry],
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )
        self.assertTrue(json.loads(json_object))
        obj = json.loads(json_object)
        self.assertEqual(obj[0]["fields"]["log"][0][:-5], now.isoformat()[:-13])
        self.assertEqual(
            obj[0]["fields"]["log"][1:],
            [
                self.subject_identifier,
                TestModelCaller.label.lower(),
                date.today().strftime("%Y-%m-%d"),
            ],
        )
