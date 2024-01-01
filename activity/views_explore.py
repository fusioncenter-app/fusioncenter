from django.shortcuts import render, redirect, get_object_or_404, reverse, get_list_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Activity,Session, Participants
from institution.models import Site, Space, Instructor
from plans.models import UserPlan, PlanPricing
from datetime import date as today_date
from django.contrib.auth.mixins import LoginRequiredMixin

import time
from itertools import groupby
from django.views import View
from django.core.paginator import Paginator

from .forms_explore import FiltersForm, SelfRegistrationForm

from urllib.parse import urlencode, urlparse, parse_qs

import re
from django.contrib import messages
from datetime import datetime, timedelta,date
from django.utils.timezone import make_aware
from django.utils import timezone
from pytz import timezone as pytz_timezone

from django.template.loader import render_to_string
from django.http import HttpResponse

def calculate_session_details(session, request_user):
    # Calculate counts for different assistance_status
    session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
    session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
    session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

    # Calculate total_participants and availability
    session.total_participants = session.registered_count + session.present_count + session.absent_count
    session.availability = session.session_capacity - session.total_participants

    # Fetch available plan pricings for the session
    available_plan_pricings = PlanPricing.objects.filter(
        plan__activities=session.activity,
        from_date__lte=session.date,
        to_date__gte=session.date,
        status='active',
    ).exists()

    # Set the boolean flag indicating whether there are available plan pricings
    session.has_available_plan_pricings = available_plan_pricings

    # Fetch participant for the request user
    if request_user and request_user.is_authenticated:
        participant = Participants.objects.filter(session=session, user=request_user).first()
        session.participant = participant if participant else None
    else:
        session.participant = None 

    return session

class ExplorePageView(View):
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'explore/htmx/explore_page_elements.html'
        return 'explore/explore_page.html'

    def get(self, request, *args, **kwargs):
        
        self.template_name = self.get_template_name()

        # Get the current URL
        current_url = request.build_absolute_uri()
        parsed_url = urlparse(current_url)

        # Update query parameters, removing the "page" parameter
        parsed_query_params = parse_qs(parsed_url.query)
        current_query_params = request.GET.dict()

        # Remove 'page' parameter from current parameters
        if 'page' in current_query_params:
            del current_query_params['page']

        # Update with current query parameters
        parsed_query_params.update(current_query_params)

        # Construct the updated URL
        updated_query = urlencode(parsed_query_params, doseq=True)
        updated_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{updated_query}"

        # print("Updated URL:", updated_url)

        # print("Updated Referring URL:", updated_referring_url)

        form = FiltersForm(request.GET)
        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            instructors = form.cleaned_data.get('instructors')

            sessions = Session.objects.filter(date__gte=today).order_by('date','from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
        else:
            # If no filters, get all sessions after today
            sessions = Session.objects.filter(date__gte=today).order_by('date')

        # Paginate the sessions first
        page = self.request.GET.get('page', 1)
        paginator = Paginator(sessions, self.paginate_by)
        paginated_sessions = paginator.get_page(page)

        # Group the paginated queryset
        grouped_sessions = {}
        for date, group in groupby(paginated_sessions, key=lambda session: session.date):
            grouped_sessions[date] = list(group)

            for session in grouped_sessions[date]:
                session = calculate_session_details(session, request.user)

        # Add current page and next page to the context
        current_page = paginated_sessions.number
        next_page = paginated_sessions.next_page_number() if paginated_sessions.has_next() else None

        context = {
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form':form,
            'updated_url':updated_url,
        }

        return render(request, self.template_name, context)
    

class SessionRegistrationView(LoginRequiredMixin, View):
    template_name = 'explore/self_session_registration.html'
    login_url = '/users/login/'

    def get(self, request, session_id):
        session = get_object_or_404(Session, pk=session_id)
        user = request.user
        form = SelfRegistrationForm(session_id=session_id, user=user)
        return render(request, self.template_name, {'form': form, 'session': session})

    def post(self, request, session_id):
        session = get_object_or_404(Session, pk=session_id)
        user = request.user
        form = SelfRegistrationForm(session_id=session_id, user=user, data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'You were registered successfully.')
            return redirect('explore_page')
        else:
            return render(request, self.template_name, {'form': form, 'session': session})


@login_required(login_url='login')
def explore_self_session_registration(request, session_id, user_plan_id):

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
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Validate if the plan pricing is still valid based on from_date and to_date
    if not plan_pricing.from_date <= session.date <= plan_pricing.to_date:
        messages.error(request, 'User plan pricing is not valid for the current date.')
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Check if the user has sessions left
    if user_plan.plan_pricing.plan.plan_type == 'limited':
        if user_plan.sessions_left <= 0:
            messages.warning(request, 'You have no sessions left in your plan.')
            session = calculate_session_details(session, request.user)
            # Render the updated inner HTML based on the new status
            updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

            # Return the updated HTML as JSON response
            return HttpResponse(updated_inner_html)
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
                session = calculate_session_details(session, request.user)
                # Render the updated inner HTML based on the new status
                updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

                # Return the updated HTML as JSON response
                return HttpResponse(updated_inner_html)

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
            session = calculate_session_details(session, request.user)

            # Render the updated inner HTML based on the new status
            updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

            # Return the updated HTML as JSON response
            return HttpResponse(updated_inner_html)
        
        else:
            messages.warning(request, 'You can not register again if you cancelled a session and the actual time is later than 2 hours before starting.')
            session = calculate_session_details(session, request.user)
            # Render the updated inner HTML based on the new status
            updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

            # Return the updated HTML as JSON response
            return HttpResponse(updated_inner_html)

    # Create the participant instance
    Participants.objects.create(
        user=user,
        session_id=session_id,
        user_plan=user_plan,
        assistance_status='registered',
        # Add other fields as needed
    )

    messages.success(request, 'Participant created successfully.')
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)

@login_required(login_url='login')
def explore_user_session_cancellation(request, session_id, user_plan_id):

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
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Check if a participant instance already exists for the user and session
    participant = Participants.objects.filter(user=user, session=session).first()
    if not participant:
        messages.warning(request, 'You are not registered for this session.')
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Check if there are more than 2 hours left for the session to start
    current_datetime = datetime.now()
    session_start_datetime = datetime.combine(session.date, session.from_time)
    time_difference = session_start_datetime - current_datetime

    if time_difference.total_seconds() < 2 * 60 * 60:  # 2 hours in seconds
        messages.warning(request, 'You can not cancel your participation as there are less than 2 hours left to start.')
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Check if there are participant instances with "present" or "absent" status
    existing_present_absent_participants = Participants.objects.filter(
        user=user,
        session=session,
        assistance_status__in=['present', 'absent']
    ).exclude(id=participant.id)

    if existing_present_absent_participants.exists():
        messages.warning(request, 'Cannot cancel registration when participants have "present" or "absent" status.')
        session = calculate_session_details(session, request.user)
        # Render the updated inner HTML based on the new status
        updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

        # Return the updated HTML as JSON response
        return HttpResponse(updated_inner_html)

    # Update the assistance status to 'cancelled'
    participant.assistance_status = 'cancelled'
    participant.save()

    messages.success(request, 'Session cancellation successful.')
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)

@login_required(login_url='login')
def explore_user_session_with_no_pricing(request, session_id,):
    user = request.user

    # Get the session using get_object_or_404
    session = get_object_or_404(Session, id=session_id)
    messages.warning(request, 'No pricing for this session, contact the owner.')
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('explore/htmx/explore_session_card_update.html', {'session': session}, request=request)

    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)


def session_info(request, session_id,):
    
    session = get_object_or_404(Session, id=session_id)
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('explore/htmx/session_info.html', {'session': session}, request=request)
    # time.sleep(5)
    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)