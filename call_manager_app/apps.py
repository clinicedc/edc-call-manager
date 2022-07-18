from django.apps import AppConfig as DjangoAppConfig

from edc_base.apps import AppConfig as EdcBaseAppConfigParent
from edc_call_manager.apps import AppConfig as EdcCallManagerAppConfigParent


class AppConfig(DjangoAppConfig):
    name = "example"
    verbose_name = "Example App"


class EdcBaseAppConfig(EdcBaseAppConfigParent):
    pass


class EdcCallManagerAppConfig(EdcCallManagerAppConfigParent):
    app_label = "example"
