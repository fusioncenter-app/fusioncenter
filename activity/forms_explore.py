# forms.py
from django import forms
from .models import Activity, Participants, Session
from institution.models import Site, Instructor
from custom_user.models import User
from plans.models import Plan,PlanPricing,UserPlan
from django.shortcuts import get_object_or_404

class FiltersForm(forms.Form):
    sites = forms.ModelMultipleChoiceField(queryset=Site.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    disciplines = forms.MultipleChoiceField(choices=Activity.TYPE_CHOICES, widget=forms.CheckboxSelectMultiple, required=False)
    instructors = forms.ModelMultipleChoiceField(queryset=Instructor.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    def __init__(self, *args, **kwargs):
        super(FiltersForm, self).__init__(*args, **kwargs)

        # Customize choice labels for instructors
        instructor_choices = []
        for instructor in self.fields['instructors'].queryset:
            label = instructor.user.get_full_name()
            instructor_choices.append((instructor.pk, label))

        self.fields['instructors'].choices = instructor_choices

class SelfRegistrationForm(forms.ModelForm):

    plan_pricing = forms.ModelChoiceField(queryset=PlanPricing.objects.none(), label='Plan Pricing')

    class Meta:
        model = Participants
        fields = ['plan_pricing']

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