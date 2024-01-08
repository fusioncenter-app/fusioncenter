from django.shortcuts import render, redirect, get_object_or_404, reverse, get_list_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Session, Participants

from datetime import date as today_date


import time
from itertools import groupby
from django.views import View
from django.core.paginator import Paginator

from .forms_sessions import SessionsFiltersForm

from urllib.parse import urlencode, urlparse, parse_qs

from .views_explore import calculate_session_details

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

class SessionsPageView(View):

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))
    
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'activity/session/htmx/session_list_elements.html'
        return 'activity/session/session_list.html'

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

        form = SessionsFiltersForm(request.user, 'today', request.GET or None)

        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            instructors = form.cleaned_data.get('instructors')
            spaces = form.cleaned_data.get('spaces')  # Add spaces to the form

            # Get sessions where the user is a participant
            participant_sessions = Participants.objects.filter(user=request.user).values_list('session', flat=True)
            sessions = Session.objects.filter(pk__in=participant_sessions, date__gte=today).order_by('date', 'from_time')

            if sites:
                if is_institution_owner(request.user):
                    # For owner, filter only sites related to their institution
                    sessions = sessions.filter(activity__site__in=sites.filter(owned_institution=request.user.owned_institution))
                elif is_institution_staff(request.user):
                    # For staff, filter only responsible sites related to the staff's profile
                    sessions = sessions.filter(activity__site__in=sites.filter(responsible_staff=request.user))
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
            if spaces:
                if is_institution_owner(request.user):
                    # For owner, filter only spaces related to their institution
                    sessions = sessions.filter(space__in=spaces.filter(site__owned_institution=request.user.owned_institution))
                elif is_institution_staff(request.user):
                    # For staff, filter only responsible spaces related to the staff's profile
                    sessions = sessions.filter(space__in=spaces.filter(site__responsible_staff=request.user))
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
            'title': 'Sessions',
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form': form,
            'updated_url': updated_url,
        }

        return render(request, self.template_name, context)
