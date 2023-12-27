# forms.py
from django import forms
from .models import Plan, PlanPricing, UserPlan
from custom_user.models import User
from activity.models import Activity
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

class CreatePlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'plan_type', 'activities']

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site', None)
        super(CreatePlanForm, self).__init__(*args, **kwargs)

        if site:
            self.fields['activities'].queryset = Activity.objects.filter(site=site)

    def clean(self):
        cleaned_data = super().clean()
        activities = cleaned_data.get('activities')

        if not activities:
            self.add_error('activities', "Select at least one activity.")

    def set_activities(self, activity_ids):
        # Manually set activities for the plan
        self.cleaned_data['activities'] = Activity.objects.filter(id__in=activity_ids)

    def save(self, commit=True):
        # Call the parent save method to save the instance
        plan = super().save(commit=False)

        # Save the plan and associated activities
        if commit:
            plan.save()
            self.save_m2m()

        return plan

class EditPlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'status', 'activities']

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site', None)
        super(EditPlanForm, self).__init__(*args, **kwargs)

        if site:
            self.fields['activities'].queryset = Activity.objects.filter(site=site)

    def set_activities(self, activity_ids):
        # Manually set activities for the plan
        self.cleaned_data['activities'] = Activity.objects.filter(id__in=activity_ids)

    def clean(self):
        cleaned_data = super().clean()
        activities = cleaned_data.get('activities')

        if not activities:
            self.add_error('activities', "Select at least one activity.")
        

class CreateUnlimitedPlanPricingForm(forms.ModelForm):
    class Meta:
        model = PlanPricing
        fields = ['name', 'from_date', 'to_date', 'price_unit', 'price_quantity']

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if from_date and to_date and from_date >= to_date:
            self.add_error('to_date', "End date must be later than the start date.")

class CreateLimitedPlanPricingForm(forms.ModelForm):
    class Meta:
        model = PlanPricing
        fields = ['name', 'from_date', 'to_date', 'sessions_quantity', 'price_unit', 'price_quantity']

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        sessions_quantity = cleaned_data.get('sessions_quantity')

        if from_date and to_date and from_date >= to_date:
            self.add_error('to_date', "End date must be later than the start date.")

        if sessions_quantity is not None and sessions_quantity <= 0:
            self.add_error('sessions_quantity', "Sessions quantity must be greater than 0.")

class EditUnlimitedPlanPricingForm(forms.ModelForm):
    class Meta:
        model = PlanPricing
        fields = ['name', 'from_date', 'to_date', 'price_unit', 'price_quantity']

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if from_date and to_date and from_date >= to_date:
            self.add_error('to_date', "End date must be later than the start date.")

class EditLimitedPlanPricingForm(forms.ModelForm):
    class Meta:
        model = PlanPricing
        fields = ['name', 'from_date', 'to_date', 'sessions_quantity', 'price_unit', 'price_quantity']

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        sessions_quantity = cleaned_data.get('sessions_quantity')

        if from_date and to_date and from_date >= to_date:
            self.add_error('to_date', "End date must be later than the start date.")

        if sessions_quantity is not None and sessions_quantity <= 0:
            self.add_error('sessions_quantity', "Sessions quantity must be greater than 0.")


class AssignUserPlanForm(forms.Form):
    email = forms.EmailField()
    payment_method = forms.ChoiceField(
        choices=UserPlan.PAYMENT_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        self.plan_pricing = kwargs.pop('plan_pricing', None)
        self.created_by = kwargs.pop('created_by', None)
        super(AssignUserPlanForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError('User with this email does not exist.')
        
        # Check if the user is already assigned to the same plan pricing
        if UserPlan.objects.filter(user=user, plan_pricing=self.plan_pricing).exists():
            raise forms.ValidationError('User is already assigned to this plan pricing.')

        return user

    def save_user_plan(self):
        user = self.cleaned_data['email']
        payment_method = self.cleaned_data['payment_method']

        # Determine sessions_left based on plan type
        if self.plan_pricing.plan.plan_type == 'unlimited':
            sessions_left = 0
        else:
            sessions_left = self.plan_pricing.sessions_quantity

        user_plan = UserPlan.objects.create(
            user=user,
            plan_pricing=self.plan_pricing,
            sessions_left=sessions_left,
            payment_method=payment_method,
            created_by=self.created_by,
        )

        return user_plan
    
class EditUserPlanForm(forms.ModelForm):
    class Meta:
        model = UserPlan
        fields = ['payment_method']

    def __init__(self, *args, **kwargs):
        super(EditUserPlanForm, self).__init__(*args, **kwargs)
        self.fields['payment_method'].choices = UserPlan.PAYMENT_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        email = self.instance.user.email

        # Check if the user is already assigned to the same plan pricing
        if UserPlan.objects.filter(user__email=email, plan_pricing=self.instance.plan_pricing).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('User is already assigned to this plan pricing.')

        return cleaned_data