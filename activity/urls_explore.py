# urls.py

from django.urls import path
from .views_explore import ( 
    ExplorePageView, SessionRegistrationView, 
    explore_self_session_registration, explore_user_session_cancellation,explore_user_session_with_no_pricing,
    session_info)

urlpatterns = [
    path('explore/', ExplorePageView.as_view(), name='explore_page'),
    path('explore/self_session_registration/<int:session_id>', SessionRegistrationView.as_view(), name='self_session_registration'),

    path('explore/explore_self_session_registration/<int:session_id>/<int:user_plan_id>/', explore_self_session_registration , name='explore_self_session_registration'),
    path('explore/explore_user_session_cancellation/<int:session_id>/<int:user_plan_id>/', explore_user_session_cancellation, name='explore_user_session_cancellation'),
    path('explore/explore_user_session_with_no_pricing/<int:session_id>/', explore_user_session_with_no_pricing, name='explore_user_session_with_no_pricing'),
    path('explore/session_info/<int:session_id>/', session_info, name='session_info'),

]
