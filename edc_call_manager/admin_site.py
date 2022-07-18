from edc_model_admin.admin_site import EdcAdminSite

from .apps import AppConfig

edc_call_manager_admin = EdcAdminSite(name="edc_call_manager_admin", app_label=AppConfig.name)


# from django.contrib.admin import AdminSite
#
#
# class EdcCallManagerAdminSite(AdminSite):
#     site_header = "Call Manager"
#     site_title = "Call Manager"
#     index_title = "Call Manager Administration"
#     site_url = "/call_manager/"
#     enable_nav_sidebar = False
#     final_catch_all_view = False
#
#
# edc_call_manager_admin = EdcCallManagerAdminSite(name="edc_call_manager_admin")
