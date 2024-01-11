from django.shortcuts import render, redirect, get_object_or_404, reverse, get_list_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Session, Participants
from institution.models import Institution, Site
from datetime import date as today_date


import time
from itertools import groupby
from django.views import View
from django.core.paginator import Paginator

from .forms_sessions import SessionsFiltersForm, InstructorSessionsFiltersForm

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

from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import date

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

            # Additional filter for owner or staff
            if is_institution_owner(request.user):
                sessions = Session.objects.filter(activity__site__in=request.user.owned_institution.sites.all(), date__gte=today).order_by('date', 'from_time')
            elif is_institution_staff(request.user):
                # If the user is staff, filter by responsible sites
                sessions = Session.objects.filter(activity__site__in=request.user.staff_profile.responsible_sites.all(), date__gte=today).order_by('date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
            if spaces:
                sessions = sessions.filter(space__in=spaces)
        else:
            # Additional filter for owner or staff
            if is_institution_owner(request.user):
                sessions = Session.objects.filter(activity__site__in=request.user.owned_institution.sites.all(), date__gte=today).order_by('date', 'from_time')
            elif is_institution_staff(request.user):
                # If the user is staff, filter by responsible sites
                sessions = Session.objects.filter(activity__site__in=request.user.staff_profile.responsible_sites.all(), date__gte=today).order_by('date', 'from_time')

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
    
class PastSessionsPageView(View):

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

        form = SessionsFiltersForm(request.user, 'yesterday', request.GET or None)

        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            instructors = form.cleaned_data.get('instructors')
            spaces = form.cleaned_data.get('spaces')  # Add spaces to the form

            # Additional filter for owner or staff
            if is_institution_owner(request.user):
                sessions = Session.objects.filter(activity__site__in=request.user.owned_institution.sites.all(), date__lt=today).order_by('-date', 'from_time')
            elif is_institution_staff(request.user):
                # If the user is staff, filter by responsible sites
                sessions = Session.objects.filter(activity__site__in=request.user.staff_profile.responsible_sites.all(), date__lt=today).order_by('-date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if instructors:
                sessions = sessions.filter(activity__instructor__in=instructors)
            if spaces:
                sessions = sessions.filter(space__in=spaces)
        else:
            # Additional filter for owner or staff
            if is_institution_owner(request.user):
                sessions = Session.objects.filter(activity__site__in=request.user.owned_institution.sites.all(), date__lt=today).order_by('-date', 'from_time')
            elif is_institution_staff(request.user):
                # If the user is staff, filter by responsible sites
                sessions = Session.objects.filter(activity__site__in=request.user.staff_profile.responsible_sites.all(), date__lt=today).order_by('-date', 'from_time')

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

        # Add current page and next page to the context
        current_page = paginated_sessions.number
        next_page = paginated_sessions.next_page_number() if paginated_sessions.has_next() else None

        context = {
            'title': 'Past Sessions',
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form': form,
            'updated_url': updated_url,
        }

        return render(request, self.template_name, context)


@login_required(login_url='login')
@user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')
def owner_session_info(request, session_id,):
    
    session = get_object_or_404(Session, id=session_id)
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('activity/session/htmx/session_info.html', {'session': session}, request=request)
    # time.sleep(5)
    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)



'''

INSTRUCTOR SESSIONS

'''

class InstructorSessionsPageView(View):

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_instructor(u), login_url='login')(view))
    
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'instructor/session/htmx/session_list_elements.html'
        return 'instructor/session/session_list.html'

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

        form = InstructorSessionsFiltersForm(request.user, 'today', request.GET or None)

        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            spaces = form.cleaned_data.get('spaces')  # Add spaces to the form

            sessions = Session.objects.filter(activity__instructor__user=request.user, date__gte=today).order_by('date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if spaces:
                sessions = sessions.filter(space__in=spaces)
        else:
            
            sessions = Session.objects.filter(activity__instructor__user=request.user, date__gte=today).order_by('date', 'from_time')

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


class InstructorPastSessionsPageView(View):

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_instructor(u), login_url='login')(view))
    
    paginate_by = 10

    def get_template_name(self):
        if self.request.htmx:
            return 'instructor/session/htmx/session_list_elements.html'
        return 'instructor/session/session_list.html'

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

        form = InstructorSessionsFiltersForm(request.user, 'yesterday', request.GET or None)

        # Filter sessions to exclude those that occurred yesterday or before
        today = today_date.today()

        if form.is_valid():
            sites = form.cleaned_data.get('sites')
            disciplines = form.cleaned_data.get('disciplines')
            spaces = form.cleaned_data.get('spaces')  # Add spaces to the form

            sessions = Session.objects.filter(activity__instructor__user=request.user, date__lt=today).order_by('-date', 'from_time')

            if sites:
                sessions = sessions.filter(activity__site__in=sites)
            if disciplines:
                sessions = sessions.filter(activity__type__in=disciplines)
            if spaces:
                sessions = sessions.filter(space__in=spaces)
        else:
            
            sessions = Session.objects.filter(activity__instructor__user=request.user, date__lt=today).order_by('-date', 'from_time')

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

        # Add current page and next page to the context
        current_page = paginated_sessions.number
        next_page = paginated_sessions.next_page_number() if paginated_sessions.has_next() else None

        context = {
            'title': 'Past Sessions',
            'grouped_sessions': grouped_sessions,
            'today': today,
            'current_page': current_page,
            'next_page': next_page,
            'form': form,
            'updated_url': updated_url,
        }

        return render(request, self.template_name, context)


@login_required(login_url='login')
@user_passes_test(lambda u: is_institution_instructor(u), login_url='login')
def instructor_session_info(request, session_id,):
    
    session = get_object_or_404(Session, id=session_id)
    session = calculate_session_details(session, request.user)
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('instructor/session/htmx/session_info.html', {'session': session}, request=request)
    # time.sleep(5)
    # Return the updated HTML as JSON response
    return HttpResponse(updated_inner_html)