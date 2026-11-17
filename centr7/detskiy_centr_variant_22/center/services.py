from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Attendance, Enrollment, MedicalCertificate, Subscription


@transaction.atomic
def enroll_child(child, group):
    child = type(child).objects.select_for_update().get(pk=child.pk)
    group = type(group).objects.select_for_update().select_related("age_range").get(pk=group.pk)
    if not group.is_active:
        raise ValidationError("Набор в эту группу закрыт.")
    if not group.age_range.min_age <= child.age <= group.age_range.max_age:
        raise ValidationError(
            f"Возраст ребёнка — {child.age} лет. Для группы требуется от "
            f"{group.age_range.min_age} до {group.age_range.max_age} лет."
        )
    if Enrollment.objects.filter(child=child, group=group, is_active=True).exists():
        raise ValidationError("Ребёнок уже записан в эту группу.")
    if group.enrollments.filter(is_active=True).count() >= group.capacity:
        raise ValidationError("В группе нет свободных мест.")
    return Enrollment.objects.create(child=child, group=group)


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
