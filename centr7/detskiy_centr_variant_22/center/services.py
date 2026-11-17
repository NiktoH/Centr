from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Attendance, Enrollment, MedicalCertificate, Subscription, StudyGroup


@transaction.atomic
def enroll_child(child, group):
    locked_group = StudyGroup.objects.select_for_update().select_related("age_range").get(pk=group.pk)

    if not locked_group.is_active:
        raise ValidationError("Набор в выбранную группу закрыт.")

    min_age = locked_group.age_range.min_age
    max_age = locked_group.age_range.max_age
    if not (min_age <= child.age <= max_age):
        raise ValidationError(
            f"Возраст ребёнка ({child.age} лет) не соответствует требованиям группы ({min_age}–{max_age} лет)."
        )

    if Enrollment.objects.filter(child=child, group=locked_group, is_active=True).exists():
        raise ValidationError("Этот ребёнок уже записан в данную группу.")

    if locked_group.free_places <= 0:
        raise ValidationError("В выбранной группе не осталось свободных мест.")

    enrollment, created = Enrollment.objects.update_or_create(
        child=child,
        group=locked_group,
        defaults={"is_active": True},
    )
    return enrollment


@transaction.atomic
def approve_certificate(certificate, reviewer):
    certificate = MedicalCertificate.objects.select_for_update().select_related(
        "attendance__subscription"
    ).get(pk=certificate.pk)
    if certificate.status != "pending":
        raise ValidationError("Эта справка уже рассмотрена.")
    attendance = Attendance.objects.select_for_update().get(pk=certificate.attendance_id)
    subscription = Subscription.objects.select_for_update().get(pk=attendance.subscription_id)
    if attendance.status != "missed":
        raise ValidationError("Вернуть занятие можно только за отмеченный пропуск.")
    illness_days = (certificate.illness_to - certificate.illness_from).days + 1
    attendance.status = "excused"
    attendance.save(update_fields=["status", "marked_at"])
    subscription.remaining_lessons = min(subscription.remaining_lessons + 1, subscription.total_lessons)
    subscription.ends_on += timedelta(days=illness_days)
    subscription.save(update_fields=["remaining_lessons", "ends_on"])
    certificate.status = "approved"
    certificate.reviewed_by = reviewer
    certificate.reviewed_at = timezone.now()
    certificate.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return subscription


@transaction.atomic
def reject_certificate(certificate, reviewer):
    certificate = MedicalCertificate.objects.select_for_update().get(pk=certificate.pk)
    if certificate.status != "pending":
        raise ValidationError("Эта справка уже рассмотрена.")
    certificate.status = "rejected"
    certificate.reviewed_by = reviewer
    certificate.reviewed_at = timezone.now()
    certificate.save(update_fields=["status", "reviewed_by", "reviewed_at"])
