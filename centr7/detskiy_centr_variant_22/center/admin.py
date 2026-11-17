from django.contrib import admin
from .models import (
    AgeRange,
    Attendance,
    Child,
    Classroom,
    Club,
    Enrollment,
    LessonSchedule,
    MedicalCertificate,
    Parent,
    StudyGroup,
    Subscription,
)


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "address")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "parent", "birth_date", "age")
    search_fields = ("last_name", "first_name", "parent__user__last_name")
    list_filter = ("birth_date",)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "direction", "is_active")
    list_filter = ("direction", "is_active")
    search_fields = ("name", "description")


@admin.register(AgeRange)
class AgeRangeAdmin(admin.ModelAdmin):
    list_display = ("title", "min_age", "max_age")


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "age_range", "classroom", "teacher", "capacity", "occupied_places", "is_active")
    list_filter = ("club", "age_range", "is_active")
    search_fields = ("title", "teacher")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("child", "group", "enrolled_at", "is_active")
    list_filter = ("is_active", "group")


@admin.register(LessonSchedule)
class LessonScheduleAdmin(admin.ModelAdmin):
    list_display = ("group", "classroom", "starts_at", "ends_at", "topic")
    list_filter = ("group", "classroom")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("title", "child", "group", "remaining_lessons", "total_lessons", "ends_on", "is_active")
    list_filter = ("is_active", "group")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("lesson", "child", "status", "subscription", "marked_at")
    list_filter = ("status", "lesson__group")


@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    list_display = ("attendance", "illness_from", "illness_to", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status",)