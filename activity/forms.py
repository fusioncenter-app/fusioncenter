from django import forms
from .models import Activity, Session, Participants
from institution.models import Instructor, Space
from plans.models import UserPlan, PlanPricing, Plan
from custom_user.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from datetime import datetime, timedelta

class ActivityCreateForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description', 'type', 'custom_capacity', 'instructor']

    def __init__(self, site_id, *args, **kwargs):
        super(ActivityCreateForm, self).__init__(*args, **kwargs)
        self.fields['instructor'].queryset = Instructor.objects.filter(institutions__sites__id=site_id)

class ActivityEditForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description', 'type', 'custom_capacity', 'instructor', 'site', 'status'] 

    def __init__(self, user, *args, **kwargs):
        super(ActivityEditForm, self).__init__(*args, **kwargs)
        
        # Assuming that the user has an 'owned_institution' attribute
        owned_institution = user.owned_institution
        
        # Filter the sites related to the owner institution
        self.fields['site'].queryset = owned_institution.sites.all()

        # Filter instructors based on the institutions related to the site
        site_id = self.initial.get('site', None)  # Get the initial site value if available
        self.fields['instructor'].queryset = Instructor.objects.filter(institutions__sites__id=site_id)

class IndividualSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'from_time', 'to_time', 'session_capacity', 'space']
        help_texts = {
            'session_capacity': 'Enter the maximum number of participants for this session. Custom Capacity: {{ activity.id }}. Space Capacity: {{ space_capacity }}.',
        }

    def __init__(self, *args, **kwargs):
        self.activity_id = kwargs.pop('activity_id')
        super(IndividualSessionForm, self).__init__(*args, **kwargs)

        # Customize the form fields
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['from_time'].widget = forms.TimeInput(attrs={'type': 'time'})
        self.fields['to_time'].widget = forms.TimeInput(attrs={'type': 'time'})

        # Set initial values for certain fields
        activity = get_object_or_404(Activity, pk=self.activity_id)
        spaces_for_activity = Space.objects.filter(site=activity.site)
        # self.fields['session_capacity'].initial = activity.custom_capacity

        # Populate the space choices with spaces for the activity site
        self.fields['space'].queryset = spaces_for_activity

        # Get a list of tuples containing the site name and space capacity
        space_capacities = [(space.name, space.max_capacity) for space in self.fields['space'].queryset]

        # Update help text with dynamic values
        self.fields['session_capacity'].help_text = f'Enter the maximum number of participants for this session: </br> <span style:"margin: 3px"><b>Activity Capacity:</b></span> {activity.custom_capacity}. </br> <b>Space Capacities:</b> {" - ".join([f"{site_name}: {capacity}" for site_name, capacity in space_capacities])}'

    def clean(self):
        cleaned_data = super().clean()
        session_capacity = cleaned_data.get('session_capacity')
        activity = get_object_or_404(Activity, pk=self.activity_id)
        custom_capacity = activity.custom_capacity

        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        space = cleaned_data.get('space')
        space_capacity = space.max_capacity

        # Validation for session capacity
        if session_capacity > custom_capacity:
            self.add_error('session_capacity', 'Session capacity cannot be greater than activity custom capacity.')

        # Validation for space capacity
        if session_capacity > space_capacity:
            self.add_error('session_capacity', 'Session capacity cannot be greater than space capacity.')

        # Validation for time order
        if from_time and to_time and from_time >= to_time:
            self.add_error('from_time', 'From time must be earlier than the to time.')

        return cleaned_data

    def save(self, commit=True):
        instance = super(IndividualSessionForm, self).save(commit=False)
        instance.activity = get_object_or_404(Activity, pk=self.activity_id)
        instance.status = 'confirmed'

        if commit:
            instance.save()

        return instance
    

class IndividualSessionEditForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'from_time', 'to_time', 'session_capacity', 'space', 'status']

    def __init__(self, *args, **kwargs):
        super(IndividualSessionEditForm, self).__init__(*args, **kwargs)

        # Customize the form fields
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['from_time'].widget = forms.TimeInput(attrs={'type': 'time'})
        self.fields['to_time'].widget = forms.TimeInput(attrs={'type': 'time'})

        # Set initial values for certain fields if needed
        session_capacity = self.instance.session_capacity if self.instance else None
        self.fields['session_capacity'].initial = session_capacity

        # Populate the space choices with spaces for the current activity site
        activity_id = self.instance.activity.id if self.instance and self.instance.activity else None
        if activity_id:
            activity = get_object_or_404(Activity, pk=activity_id)
            spaces_for_activity = Space.objects.filter(site=activity.site)
            self.fields['space'].queryset = spaces_for_activity

        # Get a list of tuples containing the site name and space capacity
        space_capacities = [(space.name, space.max_capacity) for space in self.fields['space'].queryset]

        # Update help text with dynamic values
        self.fields['session_capacity'].help_text = f'Enter the maximum number of participants for this session: </br> <span style:"margin: 3px"><b>Activity Capacity:</b></span> {activity.custom_capacity}. </br> <b>Space Capacities:</b> {" - ".join([f"{site_name}: {capacity}" for site_name, capacity in space_capacities])}'

    def clean(self):
        cleaned_data = super().clean()
        session_capacity = cleaned_data.get('session_capacity')
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        # Validate session capacity
        if session_capacity:
            activity_id = self.instance.activity.id if self.instance and self.instance.activity else None
            if activity_id:
                activity = get_object_or_404(Activity, pk=activity_id)
                custom_capacity = activity.custom_capacity
                if session_capacity > custom_capacity:
                    self.add_error('session_capacity', 'Session capacity cannot be greater than activity custom capacity.')

        # Validate time order
        if from_time and to_time and from_time >= to_time:
            self.add_error('from_time', 'From time must be earlier than the to time.')

        # Ensure date and time formats remain the same after validation errors
        # print(cleaned_data)
        return cleaned_data
    


class MultipleSessionCreationForm(forms.ModelForm):
    repeat_choices = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    repeat_option = forms.ChoiceField(choices=repeat_choices)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    from_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    to_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Session
        fields = ['space', 'session_capacity']

    def __init__(self, activity_id, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit the queryset for the space field based on the activity
        self.fields['space'].queryset = Space.objects.filter(site__activities__id=activity_id)
        self.activity_id = activity_id
        activity = get_object_or_404(Activity, pk=self.activity_id)

        # Get a list of tuples containing the site name and space capacity
        space_capacities = [(space.name, space.max_capacity) for space in self.fields['space'].queryset]

        # Update help text with dynamic values
        self.fields['session_capacity'].help_text = f'Enter the maximum number of participants for this session: </br> <span style:"margin: 3px"><b>Activity Capacity:</b></span> {activity.custom_capacity}. </br> <b>Space Capacities:</b> {" - ".join([f"{site_name}: {capacity}" for site_name, capacity in space_capacities])}'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        session_capacity = cleaned_data.get('session_capacity')
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', "End date must be greater than or equal to start date")

        repeat_option = cleaned_data.get('repeat_option')
        if repeat_option == 'daily' and not end_date:
            self.add_error('end_date', "End date is required for daily repeats")

        # Check if the session date is in the past
        if start_date and start_date < timezone.now().date():
            self.add_error('start_date', "Cannot create sessions in the past")

        # Validate session capacity
        
        activity = get_object_or_404(Activity, pk=self.activity_id)
        custom_capacity = activity.custom_capacity


        space_capacity = self.cleaned_data.get('space').max_capacity
        # print(session_capacity,custom_capacity,space_capacity)
        if session_capacity > custom_capacity:
            self.add_error('session_capacity', 'Session capacity cannot be greater than activity custom capacity.')

        if session_capacity > space_capacity or session_capacity <= 0:
            self.add_error('session_capacity', 'Invalid session capacity')
        
        # Validate times
        if from_time and to_time and from_time >= to_time:
            self.add_error('from_time', "Start time must be before end time")


        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.status = 'confirmed'
        repeat_option = self.cleaned_data.get('repeat_option')
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        from_time = self.cleaned_data.get('from_time')
        to_time = self.cleaned_data.get('to_time')
        space_capacity = self.cleaned_data.get('space').max_capacity
        session_capacity = self.cleaned_data.get('session_capacity')
        
        # Calculate the time difference using the custom function
        time_diff = self.time_diff_in_minutes(from_time, to_time)

        # Initialize session_date to start_date
        session_date = start_date

        while session_date <= end_date:
            # Check if the space is available for the selected time slot
            existing_sessions = Session.objects.filter(
                space=self.cleaned_data.get('space'),
                date=session_date,
                from_time__lt=to_time,
                to_time__gt=from_time,
            )

            if existing_sessions.exists():
                self.add_error('start_date', "Space is not available for the selected time slot")

            # Check if the session capacity is within the limits
            if session_capacity > space_capacity or session_capacity <= 0:
                self.add_error('session_capacity', "Invalid session capacity")

            # Create the session
            instance.pk = None
            instance.date = session_date
            instance.from_time = from_time
            instance.to_time = to_time
            instance.save()

            # Increment session_date based on the repeat option
            if repeat_option == 'daily':
                session_date += timedelta(days=1)
            elif repeat_option == 'weekly':
                session_date += timedelta(weeks=1)
            elif repeat_option == 'monthly':
                # Jump to the next month while maintaining the same day of the month
                session_date = session_date.replace(
                    day=start_date.day,
                    month=(session_date.month % 12) + 1,  # Ensure it stays within the range 1-12
                    year=session_date.year + (session_date.month // 12),  # Adjust the year if needed
                )

        if commit:
            instance.save()
        return instance
    
    def time_diff_in_minutes(self, time1, time2):
        # Convert time to datetime objects with a common date (today)
        datetime_today = datetime.today()
        datetime_time1 = datetime.combine(datetime_today, time1)
        datetime_time2 = datetime.combine(datetime_today, time2)

        # Calculate time difference
        diff = datetime_time2 - datetime_time1

        # Return the difference in minutes
        return diff.seconds // 60
    
class CalendarCreateSessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['activity', 'from_time', 'to_time', 'session_capacity']

    def __init__(self, space, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activity'].queryset = Activity.objects.filter(site=space.site)
        self.space_capacity = space.max_capacity

        # Update help text with dynamic values
        self.fields['session_capacity'].help_text = f'Enter the maximum number of participants for this session: Space Capacity:</b> {space.name} - {space.max_capacity} '

    def clean(self):
        cleaned_data = super().clean()
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')
        session_capacity = cleaned_data.get('session_capacity')
        activity = cleaned_data.get('activity')

        # Validate from_time and to_time
        if from_time and to_time and from_time >= to_time:
            self.add_error('from_time', "From time must be earlier than to time.")
            self.add_error('to_time', "To time must be later than from time.")

        # Validate session_capacity
        if session_capacity and session_capacity > self.space_capacity:
            self.add_error('session_capacity', "Session capacity cannot exceed the space capacity.")

        # Validate custom_capacity
        if activity:
            custom_capacity = get_object_or_404(Activity, pk=activity.pk).custom_capacity
            if session_capacity and session_capacity > custom_capacity:
                self.add_error('session_capacity', "Session capacity cannot exceed the activity capacity.")

        return cleaned_data
    

class ParticipantRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Participant Email')
    plan_pricing = forms.ModelChoiceField(queryset=PlanPricing.objects.none(), label='Plan Pricing')
    payment_method = forms.ChoiceField(choices=UserPlan.PAYMENT_CHOICES, label='Payment Method')

    class Meta:
        model = Participants
        fields = ['email', 'plan_pricing', 'payment_method']

    def __init__(self, session_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = session_id
        self.fields['plan_pricing'].queryset = self.get_available_plan_pricings()

    def get_available_plan_pricings(self):
        # Get the session based on the session_id
        session = Session.objects.get(pk=self.session_id)

        # Assuming you have a method to get available plan pricings based on criteria
        # Modify this according to your actual logic for retrieving available plan pricings
        available_plan_pricings = PlanPricing.objects.filter(
            plan__activities=session.activity,
            from_date__lte=session.date,
            to_date__gte=session.date,
            status='active',
        ).order_by('plan__plan_type', 'from_date')

        return available_plan_pricings

    def clean_email(self):
        email = self.cleaned_data['email']

        # Check if a user with the provided email already exists
        user = User.objects.filter(email=email).first()
        if not user:
            self.add_error('email', "User doesn't exist.")
        else:
            # Check if the user is already registered for the given session
            session_id = self.session_id
            existing_participant = Participants.objects.filter(session__id=session_id, user=user).first()
            if existing_participant:
                self.add_error('email', "User is already registered for this session.")

        return email
    
    def clean_plan_pricing(self):
        plan_pricing = self.cleaned_data['plan_pricing']
        email = self.cleaned_data.get('email')

        if email:
            user = User.objects.filter(email=email).first()
            if user:
                # Check if the user already has a plan with the selected plan pricing
                existing_user_plan = UserPlan.objects.filter(user=user, plan_pricing=plan_pricing).first()

                if existing_user_plan:
                    # If the existing plan is unlimited, no validation error
                    if existing_user_plan.plan_pricing.plan.plan_type == 'unlimited':
                        self.add_error('plan_pricing',"User already has this unlimited plan pricing.")

                    # If the existing plan is limited and has 0 sessions left, pass validation
                    elif existing_user_plan.sessions_left == 0:
                        return plan_pricing

                    # Otherwise, throw an error
                    else:
                        self.add_error('plan_pricing',f"User already has this plan pricing with {existing_user_plan.sessions_left}  sessions left.")
                
        return plan_pricing

    def save(self, commit=True):
        session_id = self.session_id
        

        # Use get_object_or_404 to handle the case where the session does not exist
        session = get_object_or_404(Session, pk=session_id)

        # Assuming the session is not canceled
        if session.status != 'cancelled':
            email = self.cleaned_data['email']
            plan_pricing = self.cleaned_data['plan_pricing']
            payment_method = self.cleaned_data['payment_method']

            # Get the user based on the provided email
            user, created = User.objects.get_or_create(email=email)

            # Provide the correct value for created_by (request.user if available)
            created_by = getattr(self, 'created_by', None)  # Use None if not available

            # Create a UserPlan for the user
            user_plan = UserPlan.objects.create(
                user=user,
                plan_pricing=plan_pricing,
                sessions_left=0 if plan_pricing.plan.plan_type == 'unlimited' else plan_pricing.sessions_quantity,
                created_by=created_by,  # Assuming request is available in the form
            )

            # If the plan type is limited, create a Participants instance
            if plan_pricing.plan.plan_type == 'limited':
                participant = Participants.objects.create(
                    session=session,
                    user=user,
                    user_plan=user_plan,
                )

                # Return the created participant
                return participant
            return user_plan