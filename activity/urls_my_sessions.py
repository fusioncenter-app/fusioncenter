from django.urls import path

from .views_my_sessions import MySessionsPageView, PastSessionsPageView

urlpatterns = [
    path('my_sessions/', MySessionsPageView.as_view(), name='my_sessions'),
    path('past_sessions/', PastSessionsPageView.as_view(), name='past_sessions'),
]