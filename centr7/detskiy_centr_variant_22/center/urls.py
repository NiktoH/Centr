from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "center"

urlpatterns = [
    path("", views.home, name="home"),
    path("clubs/", views.club_list, name="club_list"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="center/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="center/form.html",
            extra_context={"title": "Смена пароля"},
            success_url="/dashboard/",
        ),
        name="password_change",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("children/", views.child_list, name="child_list"),
    path("children/add/", views.child_create, name="child_create"),
    path("children/<int:pk>/edit/", views.child_update, name="child_update"),
    path("children/<int:pk>/delete/", views.child_delete, name="child_delete"),
    path("children/export/", views.export_children, name="export_children"),
    path("enrollments/", views.enrollment_list, name="enrollment_list"),
    path("enrollments/new/", views.enroll, name="enroll"),
    path("enrollments/<int:pk>/edit/", views.enrollment_update, name="enrollment_update"),
    path("enrollments/<int:pk>/delete/", views.enrollment_delete, name="enrollment_delete"),
    path("schedule/", views.schedule, name="schedule"),

]
