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
    locked_cert = (
        MedicalCertificate.objects.select_for_update()
        .select_related("attendance", "attendance__subscription")
        .get(pk=certificate.pk)
    )
    if locked_cert.status != MedicalCertificate.STATUS_PENDING:
        raise ValidationError("Эта справка уже была проверена ранее.")

    attendance = Attendance.objects.select_for_update().get(pk=locked_cert.attendance.pk)
    attendance.status = Attendance.STATUS_EXCUSED
    attendance.save(update_fields=["status", "marked_at"])

    if attendance.subscription:
        sub = Subscription.objects.select_for_update().get(pk=attendance.subscription.pk)
        sick_days = (locked_cert.illness_to - locked_cert.illness_from).days + 1
        sub.remaining_lessons += 1
        sub.ends_on = sub.ends_on + timedelta(days=sick_days)
        sub.is_active = True
        sub.save(update_fields=["remaining_lessons", "ends_on", "is_active"])

    locked_cert.status = MedicalCertificate.STATUS_APPROVED
    locked_cert.reviewed_by = reviewer
    locked_cert.reviewed_at = timezone.now()
    locked_cert.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return locked_cert


@transaction.atomic
def reject_certificate(certificate, reviewer):
    locked_cert = MedicalCertificate.objects.select_for_update().get(pk=certificate.pk)
    if locked_cert.status != MedicalCertificate.STATUS_PENDING:
        raise ValidationError("Эта справка уже была проверена ранее.")

    locked_cert.status = MedicalCertificate.STATUS_REJECTED
    locked_cert.reviewed_by = reviewer
    locked_cert.reviewed_at = timezone.now()
    locked_cert.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return locked_cert
