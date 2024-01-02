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
from .form_my_sessions import MySessionsFiltersForm

from urllib.parse import urlencode, urlparse, parse_qs

import re
from django.contrib import messages
from datetime import datetime, timedelta,date
from django.utils.timezone import make_aware
from django.utils import timezone
from pytz import timezone as pytz_timezone

from django.template.loader import render_to_string
from django.http import HttpResponse

from .views_explore import calculate_session_details

class MySessionsPageView(LoginRequiredMixin, View):
    
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'my_sessions/htmx/session_list_elements.html'
        return 'my_sessions/session_list.html'

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

        form = MySessionsFiltersForm(request.user,'today', request.GET or None )
        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            instructors = form.cleaned_data.get('instructors')

            # Get sessions where the user is a participant
            participant_sessions = Participants.objects.filter(user=request.user).values_list('session', flat=True)
            sessions = Session.objects.filter(pk__in=participant_sessions, date__gte=today).order_by('date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
        else:
            # If no filters, get all sessions where the user is a participant and after today
            participant_sessions = Participants.objects.filter(user=request.user).values_list('session', flat=True)
            sessions = Session.objects.filter(pk__in=participant_sessions, date__gte=today).order_by('date', 'from_time')

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
            'title':'My Sessions',
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form':form,
            'updated_url':updated_url,
        }

        return render(request, self.template_name, context)
    
class PastSessionsPageView(LoginRequiredMixin, View):
    
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'my_sessions/htmx/session_list_elements.html'
        return 'my_sessions/session_list.html'

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

        form = MySessionsFiltersForm(request.user,'yesterday', request.GET or None)
        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            instructors = form.cleaned_data.get('instructors')

            # Get sessions where the user is a participant
            participant_sessions = Participants.objects.filter(user=request.user).values_list('session', flat=True)
            sessions = Session.objects.filter(pk__in=participant_sessions, date__lt=today).order_by('-date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
        else:
            # If no filters, get all sessions where the user is a participant and after today
            participant_sessions = Participants.objects.filter(user=request.user).values_list('session', flat=True)
            sessions = Session.objects.filter(pk__in=participant_sessions, date__lt=today).order_by('-date', 'from_time')

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
            'title':'Past Sessions',
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form':form,
            'updated_url':updated_url,
        }

        return render(request, self.template_name, context)