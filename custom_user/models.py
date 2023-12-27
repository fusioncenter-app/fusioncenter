# custom_user.models

from django.db import models
from django_use_email_as_username.models import BaseUser, BaseUserManager

class User(BaseUser):
    objects = BaseUserManager()

    def __str__(self):
        return self.email

class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, editable=False)
    first_name = models.CharField(max_length=20, blank=False, null=True)
    last_name = models.CharField(max_length=20, blank=False, null=True)
    birth_day = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', default='default_profile_image.jpg',help_text="Add only .jpg, .jpeg and .png formats")  # Default image path
    about_me = models.TextField(max_length=200,blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=False)
    country = models.CharField(max_length=30, blank=False, null=True)
    state = models.CharField(max_length=30, blank=False, null=True)
    city = models.CharField(max_length=30,  blank=False, null=True)
    address = models.CharField(max_length=70,blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    time_zone = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f'{self.user.last_name}, {self.user.first_name} | {self.user.email}'
    
    @property
    def get_full_name(self):
        
        return f'{self.last_name}, {self.first_name}'