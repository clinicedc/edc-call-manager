from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from edc_base.views import LoginView, LogoutView

from edc_call_manager.admin import edc_call_manager_admin

from .views import HomeView

urlpatterns = [
    url(r"login", LoginView.as_view(), name="login_url"),
    url(r"logout", LogoutView.as_view(pattern_name="login_url"), name="logout_url"),
    # url(r'^call_manager/$', RedirectView.as_view(pattern_name='home_url')),
    url(
        r"^call_manager/",
        include("edc_call_manager.urls", namespace="edc-call-manager"),
    ),
    url(r"^edc/", include("edc_base.urls")),
    url(r"^admin/$", RedirectView.as_view(pattern_name="home_url")),
    url(r"^admin/", edc_call_manager_admin.urls),
    url(r"^admin/", admin.site.urls),
    url(r"^home/", HomeView.as_view(), name="home_url"),
    url(r"^", HomeView.as_view(), name="home_url"),
]


admin.site.site_header = "Example"
admin.site.site_title = "Example"
admin.site.index_title = "Example Admin"
admin.site.site_url = "/"
