from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from .views import *




urlpatterns = [
    
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
    path('register/', RegisterView.as_view(), name='register'),
    path('registration_done/', RegistrationDoneView.as_view(), name='registration_done'),
    path('profile_view/', ProfileView.as_view(), name='profile_view'),
    path('profile_edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate_account'),
    path('activate/successful/', ActivationSuccessfulView.as_view(), name='activation_successful'),
    path('activate/failed/', ActivationFailedView.as_view(), name='activation_failed'),
    path('send_verification_email_again/<str:email>/', send_verification_email_again, name='send_verification_email_again'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'),name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),name='password_reset_complete'),

    path('owner_signup/', OwnerSignupView.as_view(), name='owner_signup'),
]
