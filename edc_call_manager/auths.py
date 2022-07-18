from edc_auth.site_auths import site_auths

from .auth_objects import CALL_MANAGER, CALL_MANAGER_VIEW

site_auths.add_group(
    "edc_call_manager.view_call",
    "edc_call_manager.view_historicalcall",
    "edc_call_manager.view_log",
    "edc_call_manager.view_historicallog",
    "edc_call_manager.view_logentry",
    "edc_call_manager.view_historicallogentry",
    name=CALL_MANAGER_VIEW,
)

site_auths.add_group(
    "edc_call_manager.add_call",
    "edc_call_manager.change_call",
    "edc_call_manager.view_call",
    "edc_call_manager.view_historicalcall",
    "edc_call_manager.add_log",
    "edc_call_manager.change_log",
    "edc_call_manager.view_log",
    "edc_call_manager.view_historicallog",
    "edc_call_manager.add_logentry",
    "edc_call_manager.change_logentry",
    "edc_call_manager.view_logentry",
    "edc_call_manager.view_historicallogentry",
    name=CALL_MANAGER,
)
