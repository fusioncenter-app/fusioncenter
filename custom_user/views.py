from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, ProfileForm
from .models import User
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.contrib import messages
from django.views import View

from django.core.mail import send_mail
from django.conf import settings


class HomeView(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'home.html')


class SettingsView(View):

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, *args, **kwargs):
        return render(request, 'users/settings.html')

class LoginView(View):
    template_name = 'users/login.html'

    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to the home page
        if request.user.is_authenticated:
            return redirect('home')

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')  # Assuming you have an email field in your login form
        password = request.POST.get('password')

        # Check if the user with the given email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        error_message = "Invalid credentials. Please try again."
        is_active_error = False
        inactive_user_email = None

        if user is not None:
            if user.is_active:
                # Authenticate the user with the provided password
                try:
                    user = authenticate(request, username=email, password=password)
                    login(request, user)

                    # Redirect to the next parameter or a default URL
                    next_url = request.GET.get('next', reverse('home'))
                    return redirect(next_url)
                except:
                    # Handle invalid login (e.g., show an error message)
                    error_message = "Invalid credentials. Please try again."
                    is_active_error = False
            else:
                # User is not active; set is_active_error
                inactive_user_email = email
                error_message = "Account not verified. Check your email."
                is_active_error = True

        return render(request, self.template_name, {'email': email, 'error_message': error_message, 'is_active_error': is_active_error, 'inactive_user_email': inactive_user_email})


class LogoutView(View):

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)
    
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You logged out successfully')
        return redirect('home')


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    
    subject = 'Activate your account '
    
    html_content = render_to_string(
        'users/activation_email.html',
        {   
            'protocol':'http',
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
        }
    )
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        #subj
        subject,
        #content
        text_content,
        #from Email
        'Fusion Center',
        #List of reciepents 
        [user.email],
    )
    email.attach_alternative(html_content,"text/html")
    email.send()
    # recipient_list = [user.email]
    # send_mail(mail_subject,strip_tags(message2),'Fusion Center',[user.email],html_message=message2)
    # email = EmailMessage(mail_subject,message2,'Fusion Center | no-reply', to=[user.email])
    # email.content_subtype = 'html'
    # email.send()

def send_verification_email_again(request, email):
    if request.method == 'POST':
        # Retrieve the user with the provided email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            
            subject = 'Activate your account'
            
            html_content = render_to_string(
                'users/activation_email.html',
                {   
                    'protocol':'http',
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                }
            )
            text_content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                #subj
                subject,
                #content
                text_content,
                #from Email
                'Fusion Center',
                #List of reciepents 
                [user.email],
            )
            email.attach_alternative(html_content,"text/html")
            email.send()
            success_message = "A new verification email has been sent to your email address."
            return render(request, 'users/send_verification_email_again.html', {'success_message': success_message})
        else:
            error_message = "User with the provided email does not exist."
            return render(request, 'users/send_verification_email_again.html', {'error_message': error_message})

    return render(request, 'users/send_verification_email_again.html')



class RegisterView(View):
    template_name = 'users/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = CustomUserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')

        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_verification_email(request, user)
            return redirect('registration_done')

        return render(request, self.template_name, {'form': form})
    
class RegistrationDoneView(View):

    def get(self, request, *args, **kwargs):

        # Redirect authenticated users to the home page
        if request.user.is_authenticated:
            return redirect('home')
        
        return render(request, 'users/registration_done.html')

class ActivateAccountView(View):
    template_name_success = 'users/activation_successful.html'
    template_name_failure = 'users/activation_failed.html'

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                login(request, user)
                return redirect('activation_successful')  # Redirect to the home page after activation
            else:
                return render(request, self.template_name_failure)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(request, self.template_name_failure)
    
class ActivationSuccessfulView(View):

    template_name = 'users/activation_successful.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class ActivationFailedView(View):
    template_name = 'users/activation_failed.html'
    template_name_send_verification_email_again = 'users/send_verification_email_again.html'

    def get(self, request, email, *args, **kwargs):
        return render(request, self.template_name, {'email': email})

    def post(self, request, email, *args, **kwargs):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)

            subject = 'Activate your account'

            html_content = render_to_string(
                'users/activation_email.html',
                {
                    'protocol': 'http',
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                }
            )
            text_content = strip_tags(html_content)
            email_message = EmailMultiAlternatives(
                subject,
                text_content,
                'Fusion Center',
                [user.email],
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            success_message = "A new verification email has been sent to your email address."
            return render(request, self.template_name_send_verification_email_again, {'success_message': success_message})
        else:
            error_message = "User with the provided email does not exist."
            return render(request, self.template_name_send_verification_email_again, {'error_message': error_message})


class ProfileView(View):

    template_name = 'users/profile_view.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class ProfileEditView(View):

    template_name = 'users/profile_edit.html'
    success_template_name = 'users/profile_view.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, *args, **kwargs):
        user_profile = request.user.profile
        form = ProfileForm(instance=user_profile)
        context = {'form': form, 'user_profile': user_profile}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_profile = request.user.profile
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile edited successfully.')
            return render(request, self.success_template_name, {'message': messages.get_messages(request)})
        else:
            context = {'form': form, 'user_profile': user_profile}
            return render(request, self.template_name, context)

class OwnerSignupView(View):
    
    template_name = 'owner_signup.html'
    success_template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = name
        body = f"{phone} {email}"

        try:
            send_mail(
                subject,
                body,
                "fusioncenter.app@gmail.com",  # Sender's email address (must be a Gmail address)
                ["fusioncenter.app@gmail.com",],  # Recipient's email address (can be your own or any other)
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully. We will be contacting you soon!')
            return render(request, self.success_template_name, {'message': messages.get_messages(request)})
        except Exception as e:
            error_message = f'Error sending email: {str(e)}'
            messages.error(request, error_message)

        return render(request, self.template_name)