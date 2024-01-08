# urls.py

from django.urls import path
from .urls_explore import urlpatterns as explore_urlpatterns
from .urls_my_sessions import urlpatterns as my_sessions_urlpatterns
from .urls_sessions import urlpatterns as sessions_urlpatterns
from .views import (
    ActivityListView, CreateActivityView, EditActivityView,
    ActivityDetailView, IndividualSessionCreateView,
    IndividualSessionEditView,MultipleSessionCreateView, 
    space_calendar,DeleteSessionView,CalendarCreateSessionView,
    InstructorActivityListView, InstructorActivityDetailView, 
    SessionParticipantsView, UpdateAttendanceView,
    user_session_registration, user_session_cancellation,
    ParticipantRegistrationView)

urlpatterns = [
    
    path('activity/list/', ActivityListView.as_view(), name='activity_list'),
    path('activity/create/<int:site_id>/', CreateActivityView.as_view(), name='create_activity'),
    path('activity/edit/<int:activity_id>/', EditActivityView.as_view(), name='edit_activity'),
    path('activity/detail/<int:activity_id>/', ActivityDetailView.as_view(), name='activity_detail'),

    path('individual_session/create/<int:activity_id>/', IndividualSessionCreateView.as_view(), name='individual_session_create'),
    path('individual_session/edit/<int:activity_id>/<int:session_id>/', IndividualSessionEditView.as_view(), name='individual_session_edit'),
    path('multiple_session/create/<int:activity_id>/', MultipleSessionCreateView.as_view(), name='multiple_session_create'),

    path('calendar/<int:space_id>/',space_calendar, name='space_calendar'),
    path('session/delete/<int:session_id>/', DeleteSessionView.as_view(), name='delete_session'),

    path('calendar/create_session/<int:space_id>/<str:date>/', CalendarCreateSessionView.as_view(), name='calendar_create_session'),

    path('instructor_activity/list/<int:user_id>/', InstructorActivityListView.as_view(), name='instructor_activity_list'),
    path('instructor_activity/detail/<int:activity_id>/', InstructorActivityDetailView.as_view(), name='instructor_activity_detail'),

    path('session/participants/<int:session_id>/', SessionParticipantsView.as_view(), name='session_participants'),

    path('update_attendance/<int:participant_id>/', UpdateAttendanceView.as_view(), name='update_attendance'),

    path('user_session_registration/<int:session_id>/<int:user_plan_id>/', user_session_registration, name='user_session_registration'),
    path('user_session_cancellation/<int:session_id>/<int:user_plan_id>/', user_session_cancellation, name='user_session_cancellation'),


    path('participant_registration/<int:session_id>/', ParticipantRegistrationView.as_view(), name='participant_registration'),

] + explore_urlpatterns + my_sessions_urlpatterns + sessions_urlpatterns
