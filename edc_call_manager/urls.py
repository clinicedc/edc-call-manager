from django.urls import path, re_path

from .admin_site import edc_call_manager_admin
from .views import (
    CallSubjectCreateView,
    CallSubjectDeleteView,
    CallSubjectUpdateView,
    HomeView,
)

app_name = "edc_call_manager"


urlpatterns = [
    re_path(
        r"^(?P<caller_label>\w+)/(?P<log_pk>[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/add/$",
        CallSubjectCreateView.as_view(),
        name="call-subject-add",
    ),
    re_path(
        r"^callsubject/(?P<caller_label>\w+)/(?P<log_pk>[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/"
        "(?P<pk>[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/change/",
        CallSubjectUpdateView.as_view(),
        name="call-subject-change",
    ),
    re_path(
        r"^callsubject/(?P<caller_app_label>\w+)/(?P<caller_model_name>\w+)/"
        "(?P<pk>[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/delete/$",
        CallSubjectDeleteView.as_view(),
        name="call-subject-delete",
    ),
    path("admin/", edc_call_manager_admin.urls),
    # path("", RedirectView.as_view(url="/edc_call_manager/admin/"), name="home_url"),
    path("", HomeView.as_view(), name="home_url"),
]
