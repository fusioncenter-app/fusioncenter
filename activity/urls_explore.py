# urls.py

from django.urls import path
from .views_explore import ExplorePageView

urlpatterns = [
    path('explore/', ExplorePageView.as_view(), name='explore_page'),

]
