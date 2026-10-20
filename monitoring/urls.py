"""
URL configuration for monitoring project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from monitoringapp import views   # make sure views.index exists
from pathlib import Path
from django.http import FileResponse, Http404
from django.views.decorators.cache import never_cache


# windows notification
@never_cache
def windows_push_service_worker(request):
    sw_file = (
        Path(settings.BASE_DIR)
        / "monitoringapp"
        / "static"
        / "js"
        / "chat-sw.js"
    )

    if not sw_file.is_file():
        raise Http404("Service worker not found.")

    response = FileResponse(
        sw_file.open("rb"),
        content_type="text/javascript"
    )

    response["Service-Worker-Allowed"] = "/"
    response["X-Content-Type-Options"] = "nosniff"

    return response


urlpatterns = [

        path(
        "chat-sw.js",
        windows_push_service_worker,
        name="windows_push_service_worker"
    ),
    path('admin/', admin.site.urls),
    path('', include('monitoringapp.urls')),
    path("chat/", include("chat.urls")),
]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ⚠️ Catch-all must always be the very last
urlpatterns += [
    re_path(r'^.*$', views.index, name='catch_all'),
]
