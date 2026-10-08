from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Not This Season – Admin"
admin.site.site_title = "NTS Admin"

urlpatterns = [
    path("healthz/", lambda request: HttpResponse("ok")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("catalog.urls")),
]

if not settings.USE_CLOUDINARY:
    # Serve uploaded photos from MEDIA_ROOT (fine for a small shop; use Cloudinary/S3 for heavy traffic)
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]
