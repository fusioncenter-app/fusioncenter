from django import forms
from django.contrib.auth.hashers import make_password  # Import the password hashing function
from .models import User,Profile

class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('first_name', 'last_name','email',)  # Add other fields as needed

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.password = make_password(self.cleaned_data['password1'])  # Hash the password
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
                  'phone_number','country','state','city',
                  'address']  # You can specify which fields you want to include here