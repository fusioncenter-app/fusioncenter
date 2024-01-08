# forms.py
from django import forms
from .models import Activity, Participants, Session
from institution.models import Site, Instructor, Space, Institution
from custom_user.models import User
from plans.models import Plan,PlanPricing,UserPlan
from django.shortcuts import get_object_or_404
from .utils.permissions_utils import is_institution_owner, is_institution_staff


class SessionsFiltersForm(forms.Form):

    sites = forms.ModelMultipleChoiceField(queryset=Site.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    disciplines = forms.MultipleChoiceField(choices=Activity.TYPE_CHOICES, widget=forms.CheckboxSelectMultiple, required=False)
    instructors = forms.ModelMultipleChoiceField(queryset=Instructor.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    spaces = forms.ModelMultipleChoiceField(queryset=Space.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    def __init__(self, user, date_filter='today', *args, **kwargs):
        super(SessionsFiltersForm, self).__init__(*args, **kwargs)

        # Determine the date range based on the date_filter parameter
        from datetime import date, timedelta
        if date_filter == 'today':
            start_date = date.today()
            end_date = date.max
        elif date_filter == 'yesterday':
            start_date = date.min
            end_date = date.today() - timedelta(days=1)
        else:
            # Default to today's sessions
            start_date = date.today()
            end_date = date.max

        # Get spaces within the specified range
        if is_institution_owner(user):
            # print(user.owned_institution.__dict__)
            # Get the owned institution (assuming user.owned_institution is the institution name)
            owned_institution = get_object_or_404(Institution, name=user.owned_institution)
            
            # Get the sites associated with the institution
            associated_sites = owned_institution.sites.all()

            # Filter spaces based on the associated sites
            spaces_within_range = Space.objects.filter(site__in=associated_sites)

        elif is_institution_staff(user):
            # print(user.__dict__)

            # For staff, get responsible sites related to the staff's profile
            responsible_sites = user.staff_profile.responsible_sites.all()
            
            # Filter spaces based on the associated sites
            spaces_within_range = Space.objects.filter(site__in=responsible_sites)

        # Set the queryset for the 'spaces' field based on the determined spaces_within_range
        self.fields['spaces'].queryset = spaces_within_range

        # Get sessions within the specified date range
        sessions_within_range = Session.objects.filter(date__range=(start_date, end_date))

        # Get participants of sessions within the specified date range
        participant_sessions = Participants.objects.filter(session__in=sessions_within_range, user=user).distinct()

        # Set the queryset for the 'disciplines' field based on participants of sessions
        participant_disciplines = participant_sessions.values_list('session__activity__type', flat=True).distinct()
        self.fields['disciplines'].choices = [(discipline, discipline) for discipline in participant_disciplines]

        # Set the queryset for the 'instructors' field based on participants of sessions
        participant_instructors = participant_sessions.values_list('session__activity__instructor', flat=True).distinct()
        instructors = Instructor.objects.filter(id__in=participant_instructors).distinct()
        instructor_choices = [(instructor.pk, instructor.user.get_full_name()) for instructor in instructors]
        self.fields['instructors'].choices = instructor_choices

        # Set the queryset for the 'sites' field based on participants of sessions
        participant_sites = participant_sessions.values_list('session__activity__site', flat=True).distinct()
        if is_institution_owner(user):
            # Get the owned institution (assuming user.owned_institution is the institution name)
            owned_institution = get_object_or_404(Institution, name=user.owned_institution)
            
            # Get the sites associated with the institution
            associated_sites = owned_institution.sites.all()
            
            # For owner, include sites related to their institution

            self.fields['sites'].queryset = associated_sites
        elif is_institution_staff(user):
            # For staff, include responsible sites related to the staff's profile
            self.fields['sites'].queryset = Site.objects.filter(id__in=participant_sites).distinct()
