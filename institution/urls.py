from django.urls import path
from .views import (
    InstitutionDetailView,
    CreateSiteView,
    EditSiteView,
    CreateSpaceView,  
    EditSpaceView, 
    instructor_list,
    create_instructor,
    delete_instructor,
)


urlpatterns = [
    path('intitution/detail/', InstitutionDetailView.as_view(), name='institution_detail'),
    path('site/create_site/', CreateSiteView.as_view(), name='create_site'),
    path('site/edit_site/<int:site_id>/', EditSiteView.as_view(), name='edit_site'),
    path('space/create_space/<int:site_id>/', CreateSpaceView.as_view(), name='create_space'),
    path('space/edit_space/<int:space_id>/', EditSpaceView.as_view(), name='edit_space'),

    # # Staff URLs
    # path('staff_list/', views.staff_list, name='staff_list'),
    # path('create_staff/', views.create_staff, name='create_staff'),
    # path('edit_staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    # path('delete_staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),

    # Instructor URLs
    path('instructor_list/', instructor_list, name='instructor_list'),
    path('create_instructor/', create_instructor, name='create_instructor'),
    path('delete_instructor/<int:instructor_id>/', delete_instructor, name='delete_instructor'),
]
