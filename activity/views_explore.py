from django.shortcuts import render, redirect, get_object_or_404, reverse, get_list_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Activity,Session, Participants
from institution.models import Site, Space, Instructor
from plans.models import UserPlan
from datetime import date as today_date


from itertools import groupby
from django.views import View
from django.core.paginator import Paginator

from .forms_explore import FiltersForm

from urllib.parse import urlencode, urlparse, parse_qs

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
                # Calculate counts for different assistance_status
                session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
                session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
                session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

                # Calculate total_participants and availability
                session.total_participants = session.registered_count + session.present_count + session.absent_count
                session.availability = session.session_capacity - session.total_participants

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
