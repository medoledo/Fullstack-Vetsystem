from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & core
    path('', include('vetlogin.urls')),
    path('login/', include('vetlogin.urls')),

    # App URLs
    path('owners/', include('owners.urls')),
    path('visits/', include('visits.urls')),
    path('boarding/', include('boarding.urls')),
    path('tasks/', include('tasks.urls')),
    path('inventory/', include('inventory.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
