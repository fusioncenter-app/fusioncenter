# forms.py
from django import forms
from .models import Activity, Participants, Session
from institution.models import Site, Instructor
from custom_user.models import User
from plans.models import Plan,PlanPricing,UserPlan
from django.shortcuts import get_object_or_404
from datetime import date, timedelta

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

        disciplines = Session.objects.filter(date__gte=date.today()).values_list('activity__type', flat=True).distinct()
        self.fields['disciplines'].choices = [(discipline, discipline) for discipline in disciplines]

class SelfRegistrationForm(forms.ModelForm):
    plan_pricing = forms.ChoiceField(label='Plan Pricing', widget=forms.Select())

    class Meta:
        model = Participants
        fields = ['plan_pricing']

    def __init__(self, session_id, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = session_id
        self.user = user
        self.fields['plan_pricing'].choices = self.get_plan_pricing_choices()
        # print(self.fields['plan_pricing'].choices)

    def get_plan_pricing_choices(self):
        existing_user_plan_pricings = self.get_available_user_plan_pricings()
        available_plan_pricings = self.get_available_plan_pricings()

        choices = []

        # Track existing plan pricing ids
        existing_plan_pricing_ids = set()

        for user_plan_pricing in existing_user_plan_pricings:
            label = {
                'type': 'Existing Plans',
                'value': str(user_plan_pricing.plan_pricing),
                'price': f'{user_plan_pricing.plan_pricing.price_unit} {user_plan_pricing.plan_pricing.price_quantity}',
                'sessions_left': f'{user_plan_pricing.sessions_left}' if user_plan_pricing.plan_pricing.plan.plan_type == 'limited' else None,
            }
            choices.append((f'userplan-{user_plan_pricing.id}', label))
            existing_plan_pricing_ids.add(user_plan_pricing.plan_pricing.id)

        for plan_pricing in available_plan_pricings:
            # Drop available limited pricing if there is at least 1 existing user plan pricing with that plan pricing
            if plan_pricing.id not in existing_plan_pricing_ids:
                label = {
                    'type': 'New Plans',
                    'value': str(plan_pricing),
                    'price': f'{plan_pricing.price_unit} {plan_pricing.price_quantity}',
                    'quantity': plan_pricing.sessions_quantity,
                }
                choices.append((f'planpricing-{plan_pricing.id}', label))

        return choices

    def get_available_user_plan_pricings(self):
        session = Session.objects.get(pk=self.session_id)
        user_plan_pricings = UserPlan.objects.filter(
            user=self.user,
            plan_pricing__plan__activities=session.activity,
            plan_pricing__from_date__lte=session.date,
            plan_pricing__to_date__gte=session.date,
            plan_pricing__status='active',
            plan_pricing__plan__plan_type='limited',
            sessions_left__gt=0,
        ).order_by('plan_pricing__plan__plan_type', 'plan_pricing__from_date')

        return user_plan_pricings

    def get_available_plan_pricings(self):
        session = Session.objects.get(pk=self.session_id)
        available_plan_pricings = PlanPricing.objects.filter(
            plan__activities=session.activity,
            from_date__lte=session.date,
            to_date__gte=session.date,
            status='active',
        ).order_by('plan__plan_type', 'from_date')

        return available_plan_pricings

    def clean_plan_pricing(self):
        plan_pricing_choice = self.cleaned_data['plan_pricing']

        if not plan_pricing_choice:
            raise forms.ValidationError("Plan pricing choice is required.")

        plan_pricing_choice_split_result = plan_pricing_choice.split("-")
        choice_1 = plan_pricing_choice_split_result[0]
        choice_2 = plan_pricing_choice_split_result[1]

        if choice_1 == 'userplan':
            user_plan_id = int(choice_2)
            user_plan = UserPlan.objects.get(pk=user_plan_id)

            if user_plan.plan_pricing.plan.plan_type == 'limited' and user_plan.sessions_left <= 0:
                raise forms.ValidationError("You have no sessions left.")
            elif user_plan.plan_pricing.plan.plan_type == 'unlimited':
                raise forms.ValidationError("You can register yourself already, you have an unlimited plan to assist to this session.")
            else:
                return plan_pricing_choice

        elif choice_1 == 'planpricing':
            plan_pricing_id = int(choice_2)
            plan_pricing = PlanPricing.objects.get(pk=plan_pricing_id)

            # Validate if the plan pricing is still available
            if plan_pricing.status != 'active':
                raise forms.ValidationError("Selected plan pricing is no longer available.")

            return plan_pricing_choice

    def save(self, commit=True):
        session_id = self.session_id
        session = get_object_or_404(Session, pk=session_id)

        if session.status == 'cancelled':
            raise forms.ValidationError("Cannot register for a cancelled session.")

    
        plan_pricing_choice = self.cleaned_data['plan_pricing']
        # print(plan_pricing_choice)
        plan_pricing_choice_split_result = plan_pricing_choice.split("-")
        choice_1 = plan_pricing_choice_split_result[0]
        choice_2 = plan_pricing_choice_split_result[1]

        if choice_1 == 'userplan':
            user_plan_id = int(choice_2)
            user_plan = UserPlan.objects.get(pk=user_plan_id)

            if user_plan.plan_pricing.plan.plan_type == 'limited':
                participant = Participants.objects.create(
                    session=session,
                    user=self.user,
                    user_plan=user_plan,
                )
                return participant
            
            return user_plan

        elif choice_1 == 'planpricing':
            plan_pricing_id = int(choice_2)
            plan_pricing = PlanPricing.objects.get(pk=plan_pricing_id)

            user_plan = UserPlan.objects.create(
                user=self.user,
                plan_pricing=plan_pricing,
                sessions_left=0 if plan_pricing.plan.plan_type == 'unlimited' else plan_pricing.sessions_quantity,
                created_by=self.user,
            )
            if user_plan.plan_pricing.plan.plan_type == 'limited':
                participant = Participants.objects.create(
                        session=session,
                        user=self.user,
                        user_plan=user_plan,
                    )
                return participant
            
            return user_plan

        

        
        
