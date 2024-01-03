# forms.py

from django import forms
from .models import Site, Space, Staff, Instructor
from custom_user.models import User
from django.core.exceptions import ValidationError


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'address', 'city', 'country']


class SpaceForm(forms.ModelForm):
    class Meta:
        model = Space
        fields = ['name', 'max_capacity']


class StaffForm(forms.ModelForm):
    email = forms.EmailField(label='User Email', max_length=254)

    class Meta:
        model = Staff
        fields = ['email', 'status', 'responsible_sites']

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

        # Limit choices for responsible_sites to those related to the owner's institution
        if owner:
            self.fields['responsible_sites'].queryset = Site.objects.filter(institution=owner.profile.owned_institution)

    def clean_email(self):
        email = self.cleaned_data['email']

        # Check if the user with the given email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("User with this email does not exist.")

        # Check if the user is already a staff member
        if Staff.objects.filter(user=user).exists():
            raise ValidationError("Selected user is already a staff member.")

        return user

    def clean_status(self):
        status = self.cleaned_data['status']

        # Validate that the selected status is one of the allowed choices
        allowed_statuses = [choice[0] for choice in Staff.STATUS_CHOICES]
        if status not in allowed_statuses:
            raise ValidationError("Invalid status selected.")

        return status

    def clean_responsible_sites(self):
        responsible_sites = self.cleaned_data['responsible_sites']

        # Validate that responsible sites are related to the owner's institution
        owner_institution = self.owner.profile.owned_institution
        for site in responsible_sites.all():
            if site.institution != owner_institution:
                raise ValidationError("One or more selected sites are not related to the owner's institution.")

        return responsible_sites


class InstructorForm(forms.ModelForm):
    email = forms.EmailField(label='User Email')  # Add an EmailField for the user's email

    class Meta:
        model = Instructor
        fields = ['email']  # Use the added 'email' field in the form

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()

        # Check if the user with the provided email exists
        user_exists = User.objects.filter(email=email).exists()

        if not user_exists:
            raise forms.ValidationError("User with this email does not exist.")

        return User.objects.get(email=email)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Assign the user instance to the instance being created
        instance.user = self.cleaned_data['email']

        # Assign the institution as the one owned by the user making the request
        instance.institution = self.owner.owned_institution

        if commit:
            instance.save()

        return instance
