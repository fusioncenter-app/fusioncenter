import re
from urllib.parse import urlparse
from datetime import datetime, timedelta, date

from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import make_aware
from django.http import HttpResponse

from institution.models import Site, Space, Instructor, Staff
from plans.models import UserPlan
from .models import Activity, Session, Participants
from .forms import (
    ActivityCreateForm,
    ActivityEditForm,
    IndividualSessionForm,
    IndividualSessionEditForm,
    MultipleSessionCreationForm,
    CalendarCreateSessionForm,
    ParticipantRegistrationForm,
)
from .views_explore import *
from .views_my_sessions import *
from .views_sessions import *

from .utils.permissions_utils import (
    is_institution_owner, 
    is_institution_instructor, 
    is_institution_staff, 
    is_owner_of_site, 
    is_staff_responsible_for_site, 
    is_activity_of_owner_sites, 
    is_activity_of_staff_sites,
    is_session_of_owner_sites,
    is_session_of_staff_sites,
    is_owner_of_space,
    is_staff_responsible_for_space,
    is_instructor_of_session,
)



#Activity List
class ActivityListView(View):

    template_name = 'activity/activity/activity_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        user = request.user

        # Check if the user is an institution owner or staff
        if is_institution_owner(user):
            owned_institution = user.owned_institution
            owned_sites = owned_institution.sites.all().order_by('name')  # Order owned sites by name

        elif is_institution_staff(user):
            # For staff, retrieve the sites they are responsible for
            staff_profile = Staff.objects.get(user=user)
            owned_sites = staff_profile.responsible_sites.all().order_by('name')

        else:
            # Handle other cases or redirect to an appropriate page
            return render(request, 'permission_denied.html')
        print(owned_sites)
        # Retrieve the activities associated with those sites and order them by site
        activities_by_site = {}
        for site in owned_sites:
            activities_by_site[site] = Activity.objects.filter(site=site).order_by('type')
            print(activities_by_site[site])
        context = {
            'activities_by_site': activities_by_site,
        }

        return render(request, self.template_name, context)
    
class CreateActivityView(View):
    template_name = 'activity/activity/create_activity.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = ActivityCreateForm(site_id)
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = ActivityCreateForm(site_id, request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.site = site
            activity.save()
            return redirect('activity_list')  # Replace with your actual URL

        return render(request, self.template_name, {'form': form, 'site': site})


class EditActivityView(View):
    template_name = 'activity/activity/edit_activity.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        activity_id = kwargs['activity_id']
        activity = get_object_or_404(Activity, id=activity_id)
        site = activity.site

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = ActivityEditForm(request.user, instance=activity)
        return render(request, self.template_name, {'form': form, 'activity': activity})

    def post(self, request, *args, **kwargs):
        activity_id = kwargs['activity_id']
        activity = get_object_or_404(Activity, id=activity_id)
        site = activity.site

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = ActivityEditForm(request.user, request.POST, instance=activity)
        if form.is_valid():
            form.save()
            return redirect('activity_list')  # Replace with your actual URL

        return render(request, self.template_name, {'form': form, 'activity': activity})


class ActivityDetailView(View):
    template_name = 'activity/activity/activity_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, activity_id, *args, **kwargs):
        activity = get_object_or_404(Activity, id=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        sessions = activity.activity_sessions.order_by('date', 'from_time')

        for session in sessions:
            # Calculate counts for different assistance_status
            session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
            session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
            session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

            # Calculate total_participants and availability
            session.total_participants = session.registered_count + session.present_count + session.absent_count
            session.availability = session.session_capacity - session.total_participants

            # Calculate all_participants_present using Case expression
            if session.registered_count > 0:
                session.all_participants_present = False
            elif session.total_participants == 0:
                session.all_participants_present = None
            else:
                session.all_participants_present = True

        today = date.today()

        context = {
            'activity': activity,
            'sessions': sessions,
            'today': today,
        }

        return render(request, self.template_name, context)



class IndividualSessionCreateView(View):
    template_name = 'activity/session/individual_session_create.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, activity_id, *args, **kwargs):
        activity = get_object_or_404(Activity, id=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')
        
        form = IndividualSessionForm(activity_id=activity_id)
        return render(request, self.template_name, {'activity': activity, 'form': form})

    def post(self, request, activity_id, *args, **kwargs):
        activity = get_object_or_404(Activity, id=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        form = IndividualSessionForm(request.POST, activity_id=activity_id)
        
        if form.is_valid():
            # Save the session
            session = form.save()
            # Redirect to a success page or do something else
            return redirect('activity_detail', activity_id=activity.id)

        return render(request, self.template_name, {'activity': activity, 'form': form})

class IndividualSessionEditView(View):
    template_name = 'activity/session/individual_session_edit.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, activity_id, session_id, *args, **kwargs):
        activity = get_object_or_404(Activity, pk=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        session = get_object_or_404(Session, pk=session_id)

        # Extract values from the session object in the desired format
        initial_data = {
            'date': session.date.strftime('%Y-%m-%d'),
            'from_time': session.from_time.strftime('%H:%M'),
            'to_time': session.to_time.strftime('%H:%M'),
            'session_capacity': session.session_capacity,
            'space': session.space.id,
            'status': session.status,
        }

        form = IndividualSessionEditForm(instance=session, initial=initial_data)
        return render(request, self.template_name, {'form': form, 'activity': activity, 'session': session})

    def post(self, request, activity_id, session_id, *args, **kwargs):
        activity = get_object_or_404(Activity, pk=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        session = get_object_or_404(Session, pk=session_id)

        form = IndividualSessionEditForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            return redirect('activity_detail', activity_id=activity_id)

        return render(request, self.template_name, {'form': form, 'activity': activity, 'session': session})


class MultipleSessionCreateView(View):
    template_name = 'activity/session/multiple_session_create.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, activity_id, *args, **kwargs):
        activity = get_object_or_404(Activity, id=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        form = MultipleSessionCreationForm(activity_id)
        context = {'form': form, 'activity': activity}
        return render(request, self.template_name, context)

    def post(self, request, activity_id, *args, **kwargs):
        activity = get_object_or_404(Activity, id=activity_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_activity_of_owner_sites(request.user, activity) or is_activity_of_staff_sites(request.user, activity)):
            return render(request, 'permission_denied.html')

        form = MultipleSessionCreationForm(activity_id, request.POST)
        if form.is_valid():
            # Set the activity_id before saving
            form.instance.activity_id = activity_id
            form.save()
            return redirect('activity_detail', activity_id=activity_id)

        context = {'form': form, 'activity': activity}
        return render(request, self.template_name, context)



def get_sessions_for_week(space, year, week):
    # Calculate the start and end dates of the week
    start_date = datetime.strptime(f'{year}-{week}-1', "%Y-%W-%w").date()
    end_date = start_date + timedelta(days=6)

    # Query sessions for the specified space and date range
    sessions = space.space_sessions.filter(date__range=[start_date, end_date]).order_by('from_time')

    for session in sessions:
        # Calculate counts for different assistance_status
        session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
        session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
        session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

        # Calculate total_participants and availability
        session.total_participants = session.registered_count + session.present_count + session.absent_count
        session.availability = session.session_capacity - session.total_participants

        # Calculate all_participants_present using Case expression
        if session.registered_count > 0:
            session.all_participants_present = False
        elif session.total_participants == 0:
            session.all_participants_present = None
        else:
            session.all_participants_present = True

        # print(session.all_participants_present)

    return sessions

@login_required(login_url='login')
# @user_passes_test(lambda u: is_institution_owner(u) or is_institution_instructor(u), login_url='login')
def space_calendar(request, space_id):
    space = get_object_or_404(Space, pk=space_id)

    # Extract week and year from the query string or provide default values
    week = request.GET.get('week', 1)
    year = request.GET.get('year', datetime.now().year)

    # Convert week and year to integers
    week = int(week)
    year = int(year)

    # Calculate the start date of the current week
    start_date_current_week = datetime.strptime(f'{year}-{week}-1', "%Y-%W-%w").date()

    # Calculate the start date of the previous week
    start_date_previous_week = start_date_current_week - timedelta(weeks=1)
    previous_week = (start_date_previous_week.year, start_date_previous_week.isocalendar()[1])

    # Calculate the start date of the next week
    start_date_next_week = start_date_current_week + timedelta(weeks=1)
    next_week = (start_date_next_week.year, start_date_next_week.isocalendar()[1])

    # Calculate the list of 7 days of the current week
    days_of_week = [start_date_current_week + timedelta(days=i) for i in range(7)]

    # Assuming you have a function to get sessions for a given week
    sessions_current_week = get_sessions_for_week(space, year, week)

    # Obtaining today's date to show or not plus icon
    today = date.today()

    context = {
        'space': space,
        'year': year,
        'week': week,
        'sessions': sessions_current_week,
        'previous_week': previous_week,
        'next_week': next_week,
        'days_of_week': days_of_week,
        'today': today,
    }

    return render(request, 'activity/calendar/space_calendar.html', context)

class DeleteSessionView(View):
    template_name = 'activity/session/session_delete.html'  # Replace with your actual template name

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get_object(self, session_id):
        return get_object_or_404(Session, pk=session_id)

    def get(self, request, session_id, *args, **kwargs):
        session = self.get_object(session_id)

        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session)):
            return render(request, 'permission_denied.html')

        # Check if the session date is in the future
        if session.date < date.today():
            messages.error(request, "Cannot delete past sessions.")
            return redirect('activity_detail', activity_id=session.activity.id)

        return render(request, self.template_name, {'session': session})

    def post(self, request, session_id, *args, **kwargs):
        session = self.get_object(session_id)

        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session)):
            return render(request, 'permission_denied.html')

        # Check if the session date is in the future
        if session.date < date.today():
            messages.error(request, "Cannot delete past sessions.")
            return redirect('activity_detail', activity_id=session.activity.id)

        # Assuming you want to perform the deletion when the form is submitted
        session.delete()
        redirect_url = 'activity_list'  # Replace with the name of your activity list URL
        return redirect('activity_detail', activity_id=session.activity.id)


class CalendarCreateSessionView(View):
    template_name = 'activity/calendar/calendar_create_session.html' 

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, space_id, date, *args, **kwargs):
        space = Space.objects.get(pk=space_id)

        # Check if the user is the owner or a staff member responsible for the space
        if not (is_owner_of_space(request.user, space) or is_staff_responsible_for_space(request.user, space)):
            return render(request, 'permission_denied.html')
        
        week_number, year_number = self.calculate_week_and_year(date)
        form = CalendarCreateSessionForm(space,request.POST or None)
        context = {
            'space': space,
            'date': date,
            'form': form,
            'week_number': week_number,
            'year_number': year_number,
        }
        return render(request, self.template_name, context)

    def post(self, request, space_id, date, *args, **kwargs):
        
        space = Space.objects.get(pk=space_id)

        # Check if the user is the owner or a staff member responsible for the space
        if not (is_owner_of_space(request.user, space) or is_staff_responsible_for_space(request.user, space)):
            return render(request, 'permission_denied.html')
        
        week_number, year_number = self.calculate_week_and_year(date)
        form = CalendarCreateSessionForm(space,request.POST or None)

        if form.is_valid():
            session = form.save(commit=False)
            session.space = space
            session.date = date
            session.save()

            # Build the redirect URL with query parameters
            redirect_url = f'/space_calendar/{space_id}/?week={week_number}&year={year_number}'
            # Redirect to the manually built URL
            return redirect(redirect_url)

        else:
            context = {
                'space': space,
                'date': date,
                'form': form,
                'week_number': week_number,
                'year_number': year_number,
            }
            return render(request, self.template_name, context)

    def calculate_week_and_year(self, date):
        session_date = datetime.strptime(date, '%Y-%m-%d').date()
        week_number = session_date.isocalendar()[1]
        year_number = session_date.year
        return week_number, year_number
    
class SessionParticipantsView(View):

    template_name = 'activity/session/session_participants.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u) or is_institution_instructor(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        # Get the session or return a 404 response if not found
        session = get_object_or_404(Session, id=self.kwargs['session_id'])

        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session) or is_instructor_of_session(request.user, session)):
            return render(request, 'permission_denied.html')

        today = date.today()

        # Get the participants for the specified session
        participants = Participants.objects.filter(session=session).order_by('user__last_name')

        # Calculate the availability for the session
        registered_count = participants.filter(assistance_status='registered').count()
        present_count = participants.filter(assistance_status='present').count()
        absent_count = participants.filter(assistance_status='absent').count()
        total_participants = registered_count + present_count + absent_count
        availability = session.session_capacity - total_participants

        context = {
            'session': session,
            'participants': participants,
            'today': today,
            'availability': availability,
        }

        # Render the template with the participants and availability for the session
        return render(request, self.template_name, context)

class UpdateAttendanceView(View):

    template_name = 'activity/htmx/update_assistance.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u) or is_institution_instructor(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        # Retrieve the participant object
        participant = get_object_or_404(Participants, id=self.kwargs['participant_id'])
        session = participant.session
        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session) or is_instructor_of_session(request.user, session)):
            return render(request, 'permission_denied.html')

        # Toggle the attendance status
        if participant.assistance_status != 'cancelled':
            if participant.assistance_status == 'present':
                participant.assistance_status = 'absent'
            elif participant.assistance_status == 'absent':
                participant.assistance_status = 'registered'
            elif participant.assistance_status == 'registered':
                participant.assistance_status = 'present'

        # Update assistance_datetime and assistance_editor
        participant.assistance_datetime = timezone.now()
        participant.assistance_editor = self.request.user

        participant.save()

        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string(self.template_name, {'participant': participant}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)


@login_required(login_url='login')
# @user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u) or is_institution_instructor(u), login_url='login')
def user_session_registration(request, session_id, user_plan_id):


    # Get the referring URL
    referring_url = request.META.get('HTTP_REFERER', None)
    referring_url_parts = urlparse(referring_url)

    # Extract numeric part from the path using a regular expression
    match = re.search(r'/(\d+)/$', referring_url_parts.path)
    if match:
        user_plan_id = match.group(1)
    else:
        user_plan_id = user_plan_id

    # print(user_plan_id)

    user = request.user

    # Validate if the provided user_plan_id corresponds to the request.user
    user_plan = get_object_or_404(UserPlan, id=user_plan_id, user=user)

    # Get the session using get_object_or_404
    session = get_object_or_404(Session, id=session_id)

    plan_pricing = user_plan.plan_pricing

    # Validate if the plan pricing associated with the user plan has the same activity related to the session
    activity_id_of_session = session.activity_id
    if not plan_pricing.plan.activities.filter(id=activity_id_of_session).exists():
        messages.error(request, 'User plan pricing does not match the activity of the session.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Validate if the plan pricing is still valid based on from_date and to_date
    if not plan_pricing.from_date <= session.date <= plan_pricing.to_date:
        messages.error(request, 'User plan pricing is not valid for the current date.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Check if the user has sessions left
    if user_plan.plan_pricing.plan.plan_type == 'limited':
        if user_plan.sessions_left <= 0:
            messages.warning(request, 'You have no sessions left in your plan.')
            return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)
        else:
            # Count registered, absent, and present participants for the session
            registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
            absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()
            present_count = Participants.objects.filter(session=session, assistance_status='present').count()

            total_participants = registered_count + absent_count + present_count
            
            # print(total_participants)
            # Check if the session is already full
            if total_participants >= session.session_capacity:
                messages.warning(request, 'Sorry, the session is already full. You cannot register.')
                return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Check if a participant instance already exists for the user and session
    existing_participant = Participants.objects.filter(user=user, session=session).first()
    
    if existing_participant:
        # Get user's timezone from the cookie
        user_timezone_str = request.COOKIES.get('user_timezone', 'UTC')  # Default to UTC if not found
        user_timezone = pytz_timezone(user_timezone_str)

        # Get the current time in the user's timezone
        user_current_time = timezone.now().astimezone(user_timezone)

        # Check if it's more than 2 hours before the session
        session_datetime = datetime.combine(session.date, session.from_time)
        
        # Convert session datetime to user's timezone without changing its time
        session_datetime_aware = make_aware(session_datetime, timezone=user_timezone)
        
        # print("Session Datetime (User's Timezone):", session_datetime_aware)

        allowed_status_change_time = session_datetime_aware - timedelta(hours=2)

        # print("User Current Time:", user_current_time)
        # print("Allowed Status Change Time:", allowed_status_change_time)

        if user_current_time < allowed_status_change_time:
            existing_participant.assistance_status = 'registered'
            if existing_participant.user_plan.plan_pricing.plan.plan_type == 'limited':
                existing_participant.user_plan = get_object_or_404(UserPlan, id=user_plan_id)

            # print(existing_participant.user_plan.id)
            existing_participant.save()
            messages.success(request, 'Participant status changed to registered successfully.')
            return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)
        else:
            messages.warning(request, 'You can not register again if you cancelled a session and the actual time is later than 2 hours before starting.')
            return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Create the participant instance
    Participants.objects.create(
        user=user,
        session_id=session_id,
        user_plan=user_plan,
        assistance_status='registered',
        # Add other fields as needed
    )

    messages.success(request, 'Participant created successfully.')

    # Redirect to 'plan_pricing_sessions' with plan_pricing_id parameter
    return redirect(reverse('participant_plan_pricing_sessions', kwargs={'user_plan_id':user_plan_id}))

@login_required(login_url='login')
# @user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u) or is_institution_instructor(u), login_url='login')
def user_session_cancellation(request, session_id, user_plan_id):

    original_user_plan = user_plan_id

    # Get the referring URL
    referring_url = request.META.get('HTTP_REFERER', None)
    referring_url_parts = urlparse(referring_url)

    # Extract numeric part from the path using a regular expression
    match = re.search(r'/(\d+)/$', referring_url_parts.path)
    if match:
        user_plan_id = match.group(1)
    else:
        user_plan_id = user_plan_id

    user = request.user

    # Validate if the provided user_plan_id corresponds to the request.user
    user_plan = get_object_or_404(UserPlan, id=user_plan_id, user=user)

    # Get the session using get_object_or_404
    session = get_object_or_404(Session, id=session_id)

    plan_pricing = user_plan.plan_pricing

    # Validate if the plan pricing associated with the user plan has the same activity related to the session
    activity_id_of_session = session.activity_id
    if not plan_pricing.plan.activities.filter(id=activity_id_of_session).exists():
        messages.error(request, 'User plan pricing does not match the activity of the session.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Check if a participant instance already exists for the user and session
    participant = Participants.objects.filter(user=user, session=session).first()
    if not participant:
        messages.warning(request, 'You are not registered for this session.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Get user's timezone from the cookie
    user_timezone_str = request.COOKIES.get('user_timezone', 'UTC')  # Default to UTC if not found
    user_timezone = pytz_timezone(user_timezone_str)

    # Get the current time in the user's timezone
    user_current_time = timezone.now().astimezone(user_timezone)

    # Check if it's more than 2 hours before the session
    session_datetime = datetime.combine(session.date, session.from_time)
    
    # Convert session datetime to user's timezone without changing its time
    session_datetime_aware = make_aware(session_datetime, timezone=user_timezone)
    
    # print("Session Datetime (User's Timezone):", session_datetime_aware)

    allowed_status_change_time = session_datetime_aware - timedelta(hours=2)

    # print("User Current Time:", user_current_time)
    # print("Allowed Status Change Time:", allowed_status_change_time)

    if user_current_time > allowed_status_change_time:
        messages.warning(request, 'You cannot cancel the session as there are less than 2 hours left to start.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Check if there are participant instances with "present" or "absent" status
    existing_present_absent_participants = Participants.objects.filter(
        user=user,
        session=session,
        assistance_status__in=['present', 'absent']
    ).exclude(id=participant.id)

    if existing_present_absent_participants.exists():
        messages.warning(request, 'Cannot cancel registration when participants have "present" or "absent" status.')
        return redirect('participant_plan_pricing_sessions', user_plan_id=user_plan_id)

    # Update the assistance status to 'cancelled'
    participant.assistance_status = 'cancelled'
    participant.save()

    messages.success(request, 'Session cancellation successful.')

    # Redirect to 'plan_pricing_sessions' with plan_pricing_id parameter
    return redirect(reverse('participant_plan_pricing_sessions', kwargs={'user_plan_id':user_plan_id}))

class ParticipantRegistrationView(View):
    template_name = 'activity/session/participant_registration.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        session = get_object_or_404(Session, pk=self.kwargs['session_id'])

        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session) or is_instructor_of_session(request.user, session)):
            return render(request, 'permission_denied.html')
        
        referring_url = request.META.get('HTTP_REFERER', None)

        # Count registered, absent, and present participants for the session
        registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
        absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()
        present_count = Participants.objects.filter(session=session, assistance_status='present').count()

        total_participants = registered_count + absent_count + present_count

        # Check if the session is already full
        if total_participants >= session.session_capacity:
            messages.warning(request, 'Sorry, the session is already full. You cannot register.')
            return redirect(referring_url)

        form = ParticipantRegistrationForm(session_id=session.id)

        context = {
            'form': form,
            'session': session,
            'referring_url': referring_url,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(Session, pk=self.kwargs['session_id'])

        # Check if the user is the owner or a staff member responsible for the session
        if not (is_session_of_owner_sites(request.user, session) or is_session_of_staff_sites(request.user, session) or is_instructor_of_session(request.user, session)):
            return render(request, 'permission_denied.html')

        form = ParticipantRegistrationForm(session_id=session.id, data=request.POST)

        if form.is_valid():
            participant = form.save()
            messages.success(request, 'User registered successfully.')
            return redirect(request.POST.get('referring_url'))

        context = {
            'form': form,
            'session': session,
        }

        return render(request, self.template_name, context)


###

### Instructor Views

###
    
class InstructorActivityListView(View):
    template_name = 'instructor/instructor_activity_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_instructor(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):

        # Get the instructor associated with the user
        instructor = get_object_or_404(Instructor, user=request.user)

        # Get the activities for the specified instructor organized by site
        activities_by_site = {}
        for activity in Activity.objects.filter(instructor=instructor):
            site = activity.site
            if site not in activities_by_site:
                activities_by_site[site] = []
            activities_by_site[site].append(activity)

        # Render the template with the organized activities
        return render(request, self.template_name, {'activities_by_site': activities_by_site})

class InstructorActivityDetailView(View):
    template_name = 'instructor/instructor_activity_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_instructor(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        activity = get_object_or_404(Activity, id=self.kwargs['activity_id'])

        # Check if the logged-in user is the instructor of the activity
        if request.user != activity.instructor.user:
            # If not, you can handle unauthorized access here, for example, redirect to a different page or return a custom response
            return render(request, 'permission_denied.html')
        
        sessions = activity.sessions.all().order_by('date', 'from_time')  # Use all() to get all related sessions

        for session in sessions:
            # Calculate counts for different assistance_status
            session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
            session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
            session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

            # Calculate total_participants and availability
            session.total_participants = session.registered_count + session.present_count + session.absent_count
            session.availability = session.session_capacity - session.total_participants

            # Calculate all_participants_present using Case expression
            if session.registered_count > 0:
                session.all_participants_present = False
            elif session.total_participants == 0:
                session.all_participants_present = None
            else:
                session.all_participants_present = True

        

        # Render the template with the activity details
        return render(request, self.template_name, {'activity': activity, 'sessions': sessions, 'today': date.today()})