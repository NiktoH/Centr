from django.http import HttpResponse
from django.urls import path
from . import views


def stub_view(request, *args, **kwargs):
    return HttpResponse("Раздел в разработке (будет реализован на следующем занятии).")


urlpatterns = [
    path("", views.home, name="home"),
    path("clubs/", views.club_list, name="club_list"),
    path("register/", stub_view, name="register"),
    path("login/", stub_view, name="login"),
    path("logout/", stub_view, name="logout"),
    path("password-change/", stub_view, name="password_change"),
    path("dashboard/", stub_view, name="dashboard"),
    path("children/", stub_view, name="child_list"),
    path("children/add/", stub_view, name="child_create"),
    path("children/<int:pk>/edit/", stub_view, name="child_update"),
    path("children/<int:pk>/delete/", stub_view, name="child_delete"),
    path("children/export/", stub_view, name="export_children"),
    path("enrollments/", stub_view, name="enrollment_list"),
    path("enrollments/new/", stub_view, name="enroll"),
    path("enrollments/<int:pk>/edit/", stub_view, name="enrollment_update"),
    path("enrollments/<int:pk>/delete/", stub_view, name="enrollment_delete"),
    path("schedule/", stub_view, name="schedule"),
    path("certificates/upload/", stub_view, name="certificate_create"),
    path("staff/certificates/", stub_view, name="certificate_review"),
    path("staff/certificates/<int:pk>/<str:action>/", stub_view, name="certificate_action"),
    path("api/attendance/", stub_view, name="attendance_data"),
    path("api/groups/", stub_view, name="group_catalog_json"),
]
