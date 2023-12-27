from django.urls import path
from . import views

urlpatterns = [
    path('institution_detail/', views.institution_detail, name='institution_detail'),
    path('create_site/', views.create_site, name='create_site'),
    path('edit_site/<int:site_id>/', views.edit_site, name='edit_site'),
    path('create_space/<int:site_id>/', views.create_space, name='create_space'),
    path('edit_space/<int:space_id>/', views.edit_space, name='edit_space'),

    # # Staff URLs
    # path('staff_list/', views.staff_list, name='staff_list'),
    # path('create_staff/', views.create_staff, name='create_staff'),
    # path('edit_staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    # path('delete_staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),

    # Instructor URLs
    path('instructor_list/', views.instructor_list, name='instructor_list'),
    path('create_instructor/', views.create_instructor, name='create_instructor'),
    path('delete_instructor/<int:instructor_id>/', views.delete_instructor, name='delete_instructor'),
]
