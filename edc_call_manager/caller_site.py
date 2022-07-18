import copy
import sys
from typing import Any, Optional

from django.apps import apps as django_apps
from django.core.management.color import color_style
from django.utils.module_loading import import_module, module_has_submodule

from .exceptions import ModelCallerError
from .model_caller import ModelCaller

style = color_style()


class AlreadyRegistered(Exception):
    pass


class CallerSite:
    def __init__(self):
        self._registry = {}
        self.reset_registry()
        self.style = color_style()

    @property
    def start_models(self):
        """Return a dictionary of models used to schedule or 'start" a call or sequence of calls."""
        return self._registry["start_models"]

    @property
    def stop_models(self):
        """Return a dictionary of models used to 'close' a call or 'stop' a sequence of calls."""
        return self._registry["stop_models"]

    @property
    def model_callers(self):
        return self._registry["model_callers"]

    def register(
        self,
        caller_class: Any,
        start_model: str,
        stop_model: Optional[str] = None,
        verbose=None,
    ):
        verbose = True if verbose is None else verbose
        if start_model not in self.start_models:
            if verbose:
                sys.stdout.write(f" * registered model caller '{caller_class}'\n")
            caller = caller_class(start_model, stop_model)
            self.start_models.update({start_model: caller})
            self.model_callers.update({caller.label: caller})
            if stop_model:
                if stop_model in self.stop_models:
                    sys.stdout.write(
                        style.NOTICE(
                            "   Warning: more than one model caller uses model "
                            f"'{stop_model}' to unschedule calls.\n"
                        )
                    )
                try:
                    self.stop_models[stop_model].append(start_model)
                except KeyError:
                    self.stop_models[stop_model] = [start_model]
        else:
            raise AlreadyRegistered(
                f"A ModelCaller is already registered with model '{start_model}'."
            )

    def unregister(self, model, caller_):
        """Unregister this model caller and it's start and stop models."""
        # TODO: this does not completely reset
        del self._registry["start_models"][model]

    def verify_model(self, model, caller):
        """Confirm model has required FK."""
        if "".join(caller.call_model_fk.split("_")) == model._meta.model_name:
            pass
        else:
            try:
                getattr(model, caller.call_model_fk)
            except AttributeError as e:
                raise ModelCallerError(
                    "Model Caller was registered with model '{}'. Model requires "
                    "FK to '{}'. Got {}".format(model, caller.call_model_fk, str(e))
                )
        if caller.unscheduling_model:
            try:
                getattr(caller.unscheduling_model, caller.call_model_fk)
            except AttributeError as e:
                raise ModelCallerError(
                    "Model Caller was registered with unscheduling model '{}'. Model requires "
                    "FK to '{}'. Got {}".format(
                        caller.unscheduling_model, caller.call_model_fk, str(e)
                    )
                )

    def reset_registry(self):
        self._registry = dict(start_models={}, stop_models={}, model_callers={})

    def get_model_caller(self, label) -> ModelCaller:
        """Return a model caller class."""
        model_caller = self.model_callers.get(label)
        if not model_caller:
            raise ModelCallerError(
                f"Model caller not found using {label}. Expected one of {self.model_callers}"
            )
        return model_caller

    def schedule_calls(self, *, start_model_cls=None, start_model_obj=None):
        """Schedule a call, e.g. create a Call instance, if the model is registered as a start model."""
        model_caller = self.start_models[start_model_cls._meta.label_lower]
        model_caller.schedule_calls()
        #
        # new_calls = 0
        # total = model_caller.start_model_cls.objects.all().count()
        # for obj in tqdm(model_caller.start_model_cls.objects.all(), total=total):
        #     try:
        #         model_caller.call_model_cls.objects.get(
        #             subject_identifier=obj.subject_identifier, label=model_caller.label
        #         )
        #     except MultipleObjectsReturned:
        #         pass
        #     except ObjectDoesNotExist:
        #         site_model_callers.schedule_calls(
        #             model_cls=model_caller.start_model_cls, start_model_obj=obj
        #         )
        #         new_calls += 1

    def unschedule_calls(self, *, model_cls=None, start_model_obj=None):
        """Unschedule a call(s) if model is a stop model."""
        start_models = self.stop_models.get(model_cls._meta.label_lower, [])
        for start_model in start_models:
            model_caller = self.start_models[start_model]
            model_caller.close_all_calls(start_model_obj.subject_identifier)

    # def schedule_next_call(self, call):
    #     try:
    #         model_caller = self._registry["model_callers"].get(call.label)
    #         model_caller.schedule_next_call(call)
    #     except AttributeError as e:
    #         if "object has no attribute 'label'" not in str(e):
    #             raise AttributeError(e)

    def update_call_from_log(self, call, log_entry=None):
        model_caller = self._registry["model_callers"].get(call.label)
        model_caller.update_call_from_log(call, log_entry)

    def autodiscover(self, module_name=None):
        """Autodiscover rules from a model_callers module."""
        module_name = module_name or "model_callers"
        sys.stdout.write(" * checking for site {} ...\n".format(module_name))
        for app in django_apps.app_configs:
            try:
                mod = import_module(app)
                try:
                    before_import_registry = copy.copy(site_model_callers._registry)
                    import_module("{}.{}".format(app, module_name))
                except:
                    site_model_callers._registry = before_import_registry
                    if module_has_submodule(mod, module_name):
                        raise
            except ImportError:
                pass


site_model_callers = CallerSite()
