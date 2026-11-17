from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve # Импортируем встроенный обработчик файлов
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("static/<path:path>", serve, {"document_root": os.path.join(settings.BASE_DIR, "static")}),
    path("", include("center.urls")),
]


if settings.DEBUG:
    urlpatterns += [
        path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
