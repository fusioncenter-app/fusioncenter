from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from .views import *




urlpatterns = [
    # ... other URLs ...
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),  # Add this line for logout
    path('register/', register, name='register'),
    path('registration_done/', registration_done, name='registration_done'),
    path('profile_view/', profile_view, name='profile_view'),
    path('profile_edit/', profile_edit, name='profile_edit'),
    path('settings/', settings_view, name='settings'),
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),
    path('activate/successful/', activation_successful, name='activation_successful'),
    path('activate/failed/', activation_failed, name='activation_failed'),
    path('send_verification_email_again/<str:email>/', send_verification_email_again, name='send_verification_email_again'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'),name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),name='password_reset_complete'),

    path('owner_signup/', owner_signup, name='owner_signup'),
]
