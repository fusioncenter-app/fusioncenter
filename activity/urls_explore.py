# urls.py

from django.urls import path
from .views_explore import ExplorePageView, SessionRegistrationView

urlpatterns = [
    path('explore/', ExplorePageView.as_view(), name='explore_page'),
    path('explore/self_session_registration/<int:session_id>', SessionRegistrationView.as_view(), name='self_session_registration'),

]
