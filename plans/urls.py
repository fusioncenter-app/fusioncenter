# plans/urls.py
from django.urls import path
from .views import (
    plan_list, create_plan, edit_plan, 
    plan_detail, create_plan_pricing, edit_plan_pricing, plan_pricing_detail,
    assign_user_plan, edit_user_plan,
    
    participant_plan_list, participant_plan_detail, participant_plan_pricing_sessions,
    plan_pricing_session_list,participant_plan_pricing_session_list,
    plan_info_htmx
)

urlpatterns = [
    path('plan_list/', plan_list, name='plan_list'),
    path('create_plan/<int:site_id>/', create_plan, name='create_plan'),
    path('edit_plan/<int:plan_id>/', edit_plan, name='edit_plan'),
    path('plan_detail/<int:plan_id>/', plan_detail, name='plan_detail'),
    path('plan/<int:plan_id>/create_pricing/', create_plan_pricing, name='create_plan_pricing'),
    # path('plan/<int:plan_id>/edit_pricing/<int:pricing_id>/', edit_plan_pricing, name='edit_plan_pricing'),
    path('plan_pricing_detail/<int:plan_pricing_id>/', plan_pricing_detail, name='plan_pricing_detail'),
    path('assign_user_plan/<int:pricing_id>/', assign_user_plan, name='assign_user_plan'),
    path('edit_user_plan/<int:user_plan_id>/', edit_user_plan, name='edit_user_plan'),
    path('participant_plan_pricing_session_list/<int:user_plan_id>/', participant_plan_pricing_session_list, name='participant_plan_pricing_session_list'),

    # participant urls
    path('participant_plan_list/', participant_plan_list, name='participant_plan_list'),
    path('participant_plan_detail/<int:plan_id>/', participant_plan_detail, name='participant_plan_detail'),
    path('session_list/<int:user_plan_id>/', participant_plan_pricing_sessions, name='participant_plan_pricing_sessions'),
    path('plan_pricing_session_list/<int:plan_pricing_id>/', plan_pricing_session_list, name='plan_pricing_session_list'),
    # htmx
    path('plan_info_htmx/<int:plan_id>', plan_info_htmx, name='plan_info_htmx'),
    

]
