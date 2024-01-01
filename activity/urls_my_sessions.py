from django.urls import path

from .views_my_sessions import MySessionsPageView

urlpatterns = [
    path('my_sessions/', MySessionsPageView.as_view(), name='my_sessions'),
]