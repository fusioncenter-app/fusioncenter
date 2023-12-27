# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User, Institution, Instructor

@receiver(post_save, sender=Institution)
def assign_institution_owner_group(sender, instance, created, **kwargs):
    """
    Signal handler to assign the user to the 'InstitutionOwner' group
    when an institution is assigned to a user.
    """
    if created:
        # Check if the institution has an owner
        if instance.owner:
            # Get or create the 'InstitutionOwner' group
            institution_owner_group, created = Group.objects.get_or_create(name='InstitutionOwner')

            # Add the user to the 'InstitutionOwner' group
            instance.owner.groups.add(institution_owner_group)

# Connect the signal
post_save.connect(assign_institution_owner_group, sender=Institution)

@receiver(post_save, sender=Instructor)
def assign_instructor_group(sender, instance, created, **kwargs):
    if created:
        # Get or create the 'InstitutionInstructor' group
        instructor_group, created = Group.objects.get_or_create(name='InstitutionInstructor')

        # Add the user to the group
        instance.user.groups.add(instructor_group)