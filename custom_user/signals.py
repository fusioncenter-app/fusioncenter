# myapp/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_use_email_as_username.models import BaseUser
from .models import Profile,User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        profile = Profile.objects.create(user=instance)
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        profile.save()
