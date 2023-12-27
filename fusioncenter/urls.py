from django.contrib import admin
from django.urls import path,include
from custom_user.views import home_view, about_view

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('custom_user.urls')),
    path('', include('institution.urls')),
    path('', include('activity.urls')),
    path('', include('plans.urls')),

    path('', home_view, name='home'), 
    path('about/', about_view, name='about'), 

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)