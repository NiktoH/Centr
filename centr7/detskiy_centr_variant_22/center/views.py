from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Attendance, Club
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import MedicalCertificateForm
from .models import Attendance, MedicalCertificate
from .services import approve_certificate, reject_certificate


def home(request):
    clubs = Club.objects.filter(is_active=True)[:6]
    return render(request, "center/home.html", {"clubs": clubs})


def club_list(request):
    queryset = Club.objects.filter(is_active=True).prefetch_related("groups__age_range")
    term = request.GET.get("q", "").strip()
    direction = request.GET.get("direction", "").strip()
    selected_age = request.GET.get("age", "").strip()
    sort = request.GET.get("sort", "name")

    if term:
        queryset = queryset.filter(Q(name__icontains=term) | Q(description__icontains=term))
    if direction:
        queryset = queryset.filter(direction=direction)
    if selected_age.isdigit():
        age_val = int(selected_age)
        queryset = queryset.filter(
            groups__is_active=True,
            groups__age_range__min_age__lte=age_val,
            groups__age_range__max_age__gte=age_val,
        ).distinct()

    if sort == "direction":
        queryset = queryset.order_by("direction", "name")
    elif sort == "-id":
        queryset = queryset.order_by("-id")
    else:
        queryset = queryset.order_by("name")

    directions = Club.objects.filter(is_active=True).values_list("direction", flat=True).distinct()
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "page": page,
        "directions": directions,
        "term": term,
        "selected_age": selected_age,
    }
    return render(request, "center/club_list.html", context)

import csv
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .forms import ChildForm, EnrollmentForm, RegistrationForm
from .models import Child, Enrollment, Parent, StudyGroup, Subscription
from .services import approve_certificate, enroll_child, reject_certificate


def _get_parent(user):
    parent, _ = Parent.objects.get_or_create(user=user, defaults={"phone": ""})
    return parent


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "center/form.html", {"form": form, "title": "Регистрация родителя"})


@login_required
def dashboard(request):
    parent = _get_parent(request.user)
    children = parent.children.prefetch_related("enrollments__group")
    active_subs = Subscription.objects.filter(child__parent=parent, is_active=True)
    stats = {
        "children": children.count(),
        "groups": Enrollment.objects.filter(child__parent=parent, is_active=True).count(),
        "active_subscriptions": active_subs.count(),
        "remaining": active_subs.aggregate(total=Sum("remaining_lessons"))["total"] or 0,
    }
    return render(request, "center/dashboard.html", {"stats": stats, "children": children})


@login_required
def child_list(request):
    parent = _get_parent(request.user)
    queryset = parent.children.all()
    term = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    sort = request.GET.get("sort", "last_name")

    if term:
        queryset = queryset.filter(Q(last_name__icontains=term) | Q(first_name__icontains=term))
    if status == "enrolled":
        queryset = queryset.filter(enrollments__is_active=True).distinct()
    elif status == "free":
        queryset = queryset.exclude(enrollments__is_active=True)

    if sort == "first_name":
        queryset = queryset.order_by("first_name")
    elif sort == "-id":
        queryset = queryset.order_by("-id")
    else:
        queryset = queryset.order_by("last_name", "first_name")

    page = Paginator(queryset, 10).get_page(request.GET.get("page"))
    return render(request, "center/child_list.html", {"page": page, "term": term})


@login_required
def child_create(request):
    parent = _get_parent(request.user)
    if request.method == "POST":
        form = ChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = parent
            child.save()
            messages.success(request, "Профиль ребёнка добавлен.")
            return redirect("center:child_list")
    else:
        form = ChildForm()
    return render(request, "center/form.html", {"form": form, "title": "Добавить ребёнка"})


@login_required
def child_update(request, pk):
    parent = _get_parent(request.user)
    child = get_object_or_404(Child, pk=pk, parent=parent)
    if request.method == "POST":
        form = ChildForm(request.POST, request.FILES, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, "Данные ребёнка обновлены.")
            return redirect("center:child_list")
    else:
        form = ChildForm(instance=child)
    return render(request, "center/form.html", {"form": form, "title": "Редактировать профиль ребёнка"})


@login_required
def child_delete(request, pk):
    parent = _get_parent(request.user)
    child = get_object_or_404(Child, pk=pk, parent=parent)
    if request.method == "POST":
        child.delete()
        messages.success(request, "Профиль ребёнка удалён.")
    return redirect("child_list")


@login_required
def export_children(request):
    parent = _get_parent(request.user)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="children.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Фамилия", "Имя", "Дата рождения", "Возраст"])
    for child in parent.children.all():
        writer.writerow([child.last_name, child.first_name, child.birth_date.strftime("%d.%m.%Y"), child.age])
    return response


@login_required
def enrollment_list(request):
    parent = _get_parent(request.user)
    enrollments = Enrollment.objects.filter(child__parent=parent).select_related("child", "group__club", "group__age_range")
    return render(request, "center/enrollment_list.html", {"enrollments": enrollments})


@login_required
def enroll(request):
    parent = _get_parent(request.user)
    if request.method == "POST":
        form = EnrollmentForm(request.POST, parent=parent)
        if form.is_valid():
            try:
                enroll_child(form.cleaned_data["child"], form.cleaned_data["group"])
                messages.success(request, "Ребёнок успешно записан в группу.")
                return redirect("center:enrollment_list")
            except ValidationError as exc:
                form.add_error(None, exc.message)
    else:
        form = EnrollmentForm(parent=parent)
    return render(request, "center/form.html", {"form": form, "title": "Запись в учебную группу"})


@login_required
def enrollment_update(request, pk):
    parent = _get_parent(request.user)
    enrollment = get_object_or_404(Enrollment, pk=pk, child__parent=parent)
    if request.method == "POST":
        form = EnrollmentForm(request.POST, instance=enrollment, parent=parent)
        if form.is_valid():
            form.save()
            messages.success(request, "Запись обновлена.")
            return redirect("enrollment_list")
    else:
        form = EnrollmentForm(instance=enrollment, parent=parent)
    return render(request, "center/form.html", {"form": form, "title": "Изменить запись"})


@login_required
def enrollment_delete(request, pk):
    parent = _get_parent(request.user)
    enrollment = get_object_or_404(Enrollment, pk=pk, child__parent=parent)
    if request.method == "POST":
        enrollment.delete()
        messages.success(request, "Запись отменена.")
    return redirect("enrollment_list")


@login_required
def schedule(request):
    parent = _get_parent(request.user)
    lessons = (
        StudyGroup.objects.filter(enrollments__child__parent=parent, enrollments__is_active=True, lessons__isnull=False)
        .values(
            "title",
            "lessons__starts_at",
            "lessons__ends_at",
            "lessons__classroom__name",
            "lessons__topic",
        )
        .order_by("lessons__starts_at")
        .distinct()
    )
    return render(request, "center/schedule.html", {"lessons": lessons})

@login_required
def certificate_create(request):
    parent = _get_parent(request.user)
    if request.method == "POST":
        form = MedicalCertificateForm(request.POST, request.FILES, parent=parent)
        if form.is_valid():
            form.save()
            messages.success(request, "Медицинская справка отправлена на проверку администратору.")
            return redirect("dashboard")
    else:
        form = MedicalCertificateForm(parent=parent)
    return render(request, "center/form.html", {"form": form, "title": "Загрузить медицинскую справку"})


@staff_member_required
def certificate_review(request):
    certificates = MedicalCertificate.objects.select_related(
        "attendance__child",
        "attendance__lesson__group",
        "reviewed_by",
    )
    return render(request, "center/certificate_review.html", {"certificates": certificates})


@staff_member_required
@require_POST
def certificate_action(request, pk, action):
    certificate = get_object_or_404(MedicalCertificate, pk=pk)
    try:
        if action == "approve":
            approve_certificate(certificate, request.user)
            messages.success(request, "Справка подтверждена, занятие возвращено на баланс абонемента.")
        elif action == "reject":
            reject_certificate(certificate, request.user)
            messages.info(request, "Справка отклонена.")
    except ValidationError as exc:
        messages.error(request, exc.message)
    return redirect("certificate_review")


@login_required
def attendance_data(request):
    parent = _get_parent(request.user)
    qs = Attendance.objects.filter(child__parent=parent)
    data = {
        "present": qs.filter(status=Attendance.STATUS_PRESENT).count(),
        "missed": qs.filter(status=Attendance.STATUS_MISSED).count(),
        "excused": qs.filter(status=Attendance.STATUS_EXCUSED).count(),
    }
    return JsonResponse(data)


def group_catalog_json(request):
    groups = StudyGroup.objects.filter(is_active=True).select_related("club", "age_range")
    payload = [
        {
            "id": g.id,
            "title": g.title,
            "club": g.club.name,
            "age_range": f"{g.age_range.min_age}–{g.age_range.max_age} лет",
            "free_places": g.free_places,
        }
        for g in groups
    ]
    return JsonResponse({"groups": payload})
