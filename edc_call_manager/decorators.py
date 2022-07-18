def register(start_model, stop_model=None, **kwargs):
    """
    Registers the given model class and wrapped ModelCaller class with
    site_model_callers:

    @register(Antenatal)
    class AntenatalModelCaller(ModelCaller):
        pass
    """
    from .model_caller import ModelCaller
    from .caller_site import site_model_callers

    def _model_caller_wrapper(caller_class):

        if not issubclass(caller_class, ModelCaller):
            raise ValueError("Wrapped class must subclass ModelCaller.")
        site_model_callers.register(caller_class, start_model, stop_model)

        return caller_class

    return _model_caller_wrapper
