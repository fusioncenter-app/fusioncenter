# urls.py

from django.urls import path
from .urls_explore import urlpatterns as explore_urlpatterns
from .views import (
    activity_list, create_activity, edit_activity,
    activity_detail,individual_session_create,
    individual_session_edit,multiple_session_create, 
    space_calendar,delete_session,calendar_create_session,
    instructor_activity_list, instructor_activity_detail, 
    session_participants, update_attendance,
    user_session_registration, user_session_cancellation,
    participant_registration)

urlpatterns = [
    # Other URL patterns
    path('activity_list/', activity_list, name='activity_list'),
    path('create_activity/<int:site_id>/', create_activity, name='create_activity'),
    path('edit_activity/<int:activity_id>/', edit_activity, name='edit_activity'),
    path('activity_detail/<int:activity_id>/', activity_detail, name='activity_detail'),

    path('individual_session_create/<int:activity_id>/', individual_session_create, name='individual_session_create'),
    path('individual_session_edit/<int:activity_id>/<int:session_id>/', individual_session_edit, name='individual_session_edit'),
    path('multiple_session_create/<int:activity_id>/', multiple_session_create, name='multiple_session_create'),

    path('space_calendar/<int:space_id>/', space_calendar, name='space_calendar'),
    path('session_delete/<int:session_id>/', delete_session, name='delete_session'),

    path('calendar_create_session/<int:space_id>/<str:date>/', calendar_create_session, name='calendar_create_session'),

    path('instructor_activity_list/<int:user_id>/', instructor_activity_list, name='instructor_activity_list'),
    path('instructor_activity_detail/<int:activity_id>/', instructor_activity_detail, name='instructor_activity_detail'),
    path('session_participants/<int:session_id>/', session_participants, name='session_participants'),

    path('update_attendance/<int:participant_id>/', update_attendance, name='update_attendance'),

    path('user_session_registration/<int:session_id>/<int:user_plan_id>/', user_session_registration, name='user_session_registration'),
    path('user_session_cancellation/<int:session_id>/<int:user_plan_id>/', user_session_cancellation, name='user_session_cancellation'),


    path('participant_registration/<int:session_id>/', participant_registration, name='participant_registration'),

] + explore_urlpatterns