# activity/urls_sessions.py

from django.urls import path

from .views_sessions import SessionsPageView, PastSessionsPageView, owner_session_info, InstructorSessionsPageView, InstructorPastSessionsPageView,instructor_session_info

urlpatterns = [
    path('owner_session/list/', SessionsPageView.as_view(), name='owner_session_list'),
    path('past_owner_session/list/', PastSessionsPageView.as_view(), name='past_owner_session_list'),
    path('owner_session_info/<int:session_id>/', owner_session_info, name='owner_session_info'),

    # INSTRUCTOR SESSIONS
    path('instructor_session/list/', InstructorSessionsPageView.as_view(), name='instructor_session_list'),
    path('past_instructor_session/list/', InstructorPastSessionsPageView.as_view(), name='past_instructor_session_list'),
    path('instructor_session_info/<int:session_id>/', instructor_session_info, name='instructor_session_info'),

]
