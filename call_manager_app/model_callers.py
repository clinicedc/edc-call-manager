from edc_registration.models import RegisteredSubject

from edc_call_manager.decorators import register
from edc_call_manager.model_caller import ModelCaller

from .models import Locator, TestModel, TestStartModel, TestStopModel


@register(TestStartModel, TestStopModel)
class TestModelCaller1(ModelCaller):
    verbose_name = "Subject follow-up for test start model"
    label = "TestModelCaller1"
    app_label = "edc_call_manager_example"
    locator_model = Locator
    subject_model = RegisteredSubject


@register(TestModel, TestStopModel)
class TestModelCaller2(ModelCaller):
    verbose_name = "Subject follow-up for test model"
    label = "TestModelCaller2"
    app_label = "edc_call_manager_example"
    locator_model = Locator
    subject_model = RegisteredSubject
