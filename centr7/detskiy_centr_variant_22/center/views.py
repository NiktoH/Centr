from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Club


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
