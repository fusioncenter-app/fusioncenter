from django.urls import path
from .views import (
    InstitutionDetailView,
    CreateSiteView,
    EditSiteView,
    CreateSpaceView,  
    EditSpaceView, 
    InstructorListView,
    CreateInstructorView,
    DeleteInstructorView,


    StaffListView,
    CreateStaffView,
    EditStaffView,
    DeleteStaffView,
)


urlpatterns = [
    #Institution Urls
    path('institution/detail/', InstitutionDetailView.as_view(), name='institution_detail'),

    #Site Urls
    path('site/create/', CreateSiteView.as_view(), name='create_site'),
    path('site/edit/<int:site_id>/', EditSiteView.as_view(), name='edit_site'),

    #Space Urls
    path('space/create/<int:site_id>/', CreateSpaceView.as_view(), name='create_space'),
    path('space/edit/<int:space_id>/', EditSpaceView.as_view(), name='edit_space'),

    # Staff URLs
    path('staff/list/', StaffListView.as_view(), name='staff_list'),
    path('staff/create/', CreateStaffView.as_view(), name='create_staff'),
    path('staff/edit/<int:staff_id>/', EditStaffView.as_view(), name='edit_staff'),
    path('staff/delete/<int:staff_id>/', DeleteStaffView.as_view(), name='delete_staff'),

    # Instructor URLs
    path('instructor/list/', InstructorListView.as_view(), name='instructor_list'),
    path('instructor/create/', CreateInstructorView.as_view(), name='create_instructor'),
    path('instructor/delete/<int:instructor_id>/', DeleteInstructorView.as_view(), name='delete_instructor'),
]
