from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from edc_constants.constants import CLOSED

from ..caller_site import site_model_callers


@receiver(post_save, weak=False, dispatch_uid="edc_call_manager_model_caller_on_post_save")
def edc_call_manager_model_caller_on_post_save(
    sender, instance, raw, created, using, update_fields, **kwargs
):
    """A signal that acts on start and stop models on create."""
    if not raw and created:
        label_lower = sender._meta.label_lower
        if "historical" not in label_lower and label_lower in site_model_callers.start_models:
            site_model_callers.schedule_calls(model_cls=sender, start_model_obj=instance)
            site_model_callers.unschedule_calls(model_cls=sender, start_model_obj=instance)


@receiver(post_save, weak=False, dispatch_uid="edc_call_manager_call_on_post_save")
def edc_call_manager_call_on_post_save(
    sender, instance, raw, created, using, update_fields, **kwargs
):
    """A signal that acts on the Call model and schedules a new call
    if the current one is closed and configured to repeat on
    the model_caller.
    """
    if not raw and not created:
        try:
            label_lower = sender._meta.label_lower
        except AttributeError:
            pass
        else:
            if "historical" not in label_lower:
                try:
                    call_status = instance.call_status == CLOSED
                except AttributeError as e:
                    if "has no attribute 'call_status'" not in str(e):
                        raise
                    pass
                else:
                    site_model_callers.unschedule_calls(
                        model_cls=sender, start_model_obj=instance
                    )
                    if call_status == CLOSED:
                        site_model_callers.schedule_next_call(instance)


@receiver(post_save, weak=False, dispatch_uid="edc_call_manager_log_entry_on_post_save")
def edc_call_manager_log_entry_on_post_save(sender, instance, raw, created, using, **kwargs):
    """Updates call after a log entry ('call_status', 'call_attempts', 'call_outcome')."""
    pass
    # if not raw and "historical" not in sender._meta.label_lower:
    #     try:
    #         site_model_callers.update_call_from_log(instance.log.call, log_entry=instance)
    #         model_caller = site_model_callers.get_model_caller(sender._meta.label_lower)
    #         if model_caller:
    #             model_caller.appointment_handler(instance.log.call, log_entry=instance)
    #     except AttributeError as e:
    #         if "has no attribute 'log'" not in str(e):
    #             raise AttributeError(e)
