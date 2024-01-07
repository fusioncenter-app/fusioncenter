from django.contrib import admin
from django.urls import path,include
from custom_user.views import HomeView,OwnerSignupView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('custom_user.urls')),
    path('', include('institution.urls')),
    path('', include('activity.urls')),
    path('', include('plans.urls')),

    path('', HomeView.as_view(), name='home'), 
    path('owner_signup/', OwnerSignupView.as_view(), name='owner_signup'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)