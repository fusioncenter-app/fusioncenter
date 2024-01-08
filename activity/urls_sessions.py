# activity/urls_sessions.py

from django.urls import path

from .views_sessions import SessionsPageView

urlpatterns = [
    path('owner_session/list/', SessionsPageView.as_view(), name='owner_session_list'),
]
