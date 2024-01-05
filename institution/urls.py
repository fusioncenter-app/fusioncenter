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
    create_staff,
    edit_staff,
    delete_staff
)


urlpatterns = [
    #Institution Urls
    path('institution/detail/', InstitutionDetailView.as_view(), name='institution_detail'),

    #Site Urls
    path('site/create_site/', CreateSiteView.as_view(), name='create_site'),
    path('site/edit_site/<int:site_id>/', EditSiteView.as_view(), name='edit_site'),

    #Space Urls
    path('space/create_space/<int:site_id>/', CreateSpaceView.as_view(), name='create_space'),
    path('space/edit_space/<int:space_id>/', EditSpaceView.as_view(), name='edit_space'),

    # Staff URLs
    path('staff/list/', StaffListView.as_view(), name='staff_list'),
    path('create_staff/', create_staff, name='create_staff'),
    path('edit_staff/<int:staff_id>/', edit_staff, name='edit_staff'),
    path('delete_staff/<int:staff_id>/', delete_staff, name='delete_staff'),

    # Instructor URLs
    path('instructor_list/', InstructorListView.as_view(), name='instructor_list'),
    path('create_instructor/', CreateInstructorView.as_view(), name='create_instructor'),
    path('delete_instructor/<int:instructor_id>/', DeleteInstructorView.as_view(), name='delete_instructor'),
]
