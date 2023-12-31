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

from django.core.mail import send_mail
from django.conf import settings


def home_view(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

@login_required(login_url='login')
def settings_view(request):
    return render(request, 'users/settings.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home') 
    
    if request.method == 'POST':
        email = request.POST['email']  # Assuming you have an email field in your login form
        password = request.POST['password']

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

        return render(request, 'users/login.html', {'email':email,'error_message': error_message, 'is_active_error': is_active_error, 'inactive_user_email': inactive_user_email})
        
        
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to the home page after logout


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



def register(request):
    if request.user.is_authenticated:
        return redirect('home') 
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User is not active until they verify their email
            user.save()
            send_verification_email(request, user)
            return redirect('registration_done')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def registration_done(request):
    return render(request, 'users/registration_done.html')

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('activation_successful')  # Redirect to the home page after activation
        else:
            return render(request, 'users/activation_failed.html')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'users/activation_failed.html')
    
@login_required(login_url='login')
def activation_successful(request):
    return render(request, 'users/activation_successful.html')

def activation_failed(request,email):
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
        
    return render(request, 'users/activation_failed.html')


@login_required(login_url='login')
def profile_view(request):
    return render(request, 'users/profile_view.html')

@login_required(login_url='login')
def profile_edit(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        # print(form)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile edited successfuly.')
            return render(request, 'users/profile_view.html', {'message': messages.get_messages(request)})
            # return redirect('profile_view')  # Redirect to the user's profile page after editing
    
        else:   

            context = {
                'form': form , 
                'user_profile':user_profile,
            }
            return render(request, 'users/profile_edit.html', context)
    
    elif request.method == 'GET':
        form = ProfileForm(instance=user_profile)

        context = {
            
            'form': form , 
            'user_profile':user_profile,
        }
        return render(request, 'users/profile_edit.html', context)


def owner_signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = name
        body = phone + " " + email

        try:
            send_mail(
                subject,
                body,
                "fusioncenter.app@gmail.com",  # Sender's email address (must be a Gmail address)
                ["fusioncenter.app@gmail.com",],  # Recipient's email address (can be your own or any other)
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully. We will be contacting you soon!')
            return render(request, 'home.html', {'message': messages.get_messages(request)})
        except Exception as e:
            error_message = f'Error sending email: {str(e)}'
            messages.error(request, error_message)

    return render(request, 'owner_signup.html')