# plans/urls.py
from django.urls import path
from .views import (

    PlanListView, CreatePlanView, EditPlanView, 
    PlanDetailView, CreatePlanPricingView, EditPlanPricingView, PlanPricingDetailView,
    AssignUserPlanView, EditUserPlanView, PlanPricingSessionListView,ParticipantPlanPricingSessionListView,
    
    ParticipantPlanListView, ParticipantPlanDetailView, ParticipantPlanPricingSessionsView,
    
    plan_info_htmx
)

urlpatterns = [
    path('plan/list/', PlanListView.as_view(), name='plan_list'),
    path('plan/create/<int:site_id>/', CreatePlanView.as_view(), name='create_plan'),
    path('plan/edit/<int:plan_id>/', EditPlanView.as_view(), name='edit_plan'),
    path('plan/detail/<int:plan_id>/', PlanDetailView.as_view(), name='plan_detail'),
    path('plan_pricing/create/<int:plan_id>/', CreatePlanPricingView.as_view(), name='create_plan_pricing'),
    # path('plan/<int:plan_id>/edit_pricing/<int:pricing_id>/', EditPlanPricingView.as_view(), name='edit_plan_pricing'),
    path('plan_pricing/detail/<int:plan_pricing_id>/', PlanPricingDetailView.as_view(), name='plan_pricing_detail'),
    path('user_plan/create/<int:pricing_id>/', AssignUserPlanView.as_view(), name='assign_user_plan'),
    path('user_plan/edit/<int:user_plan_id>/', EditUserPlanView.as_view(), name='edit_user_plan'),

    path('plan_pricing/session/list/<int:plan_pricing_id>/', PlanPricingSessionListView.as_view(), name='plan_pricing_session_list'),
    path('plan_pricing/participant_session/list/<int:user_plan_id>/', ParticipantPlanPricingSessionListView.as_view(), name='participant_plan_pricing_session_list'),

    # participant urls
    path('participant_plan/list/', ParticipantPlanListView.as_view(), name='participant_plan_list'),
    path('participant_plan/detail/<int:plan_id>/', ParticipantPlanDetailView.as_view(), name='participant_plan_detail'),
    path('participant_plan_pricing/session/list/<int:user_plan_id>/', ParticipantPlanPricingSessionsView.as_view(), name='participant_plan_pricing_sessions'),
    # path('plan_pricing_session_list/<int:plan_pricing_id>/', PlanPricingSessionListView.as_view(), name='plan_pricing_session_list'),
    
    # htmx
    path('plan_info_htmx/<int:plan_id>', plan_info_htmx, name='plan_info_htmx'),
    

]
