from django.urls import path

from .views_my_sessions import MySessionsPageView, PastSessionsPageView, my_session_info

urlpatterns = [
    path('my_sessions/', MySessionsPageView.as_view(), name='my_sessions'),
    path('past_sessions/', PastSessionsPageView.as_view(), name='past_sessions'),
    path('my_session_info/<int:session_id>/', my_session_info, name='my_session_info'),
]