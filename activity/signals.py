# activity/signals.py

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from activity.models import Session, Participants
from plans.models import UserPlan
from .utils.signal_utils import should_participate, add_participant, remove_participant

@receiver(post_save, sender=Session)
def update_participants(sender, instance, **kwargs):
    """
    Signal handler to update participants based on UserPlans when a Session is added or edited.
    """
    # Get all participants for the session
    participants = Participants.objects.filter(session=instance)

    # Iterate through participants and check if they should still participate
    for participant in participants:
        user = participant.user
        if not should_participate(user, instance):
            # Remove participant if they should not participate
            remove_participant(participant)
    
    # Get the UserPlans related to the session's activity
    user_plans = UserPlan.objects.filter(plan_pricing__plan__activities=instance.activity)

    # Iterate through UserPlans and update participants based on logic
    for user_plan in user_plans:
        user = user_plan.user
        if should_participate(user, instance):
            # Add participant if they should participate
            add_participant(user, instance, user_plan)


@receiver(post_save, sender=Participants)
def update_sessions_left_on_participant_create(sender, instance, created, **kwargs):
    if created:
        user_plan = instance.user_plan
        if user_plan.plan_pricing.plan.plan_type == 'limited':
            # Increment sessions_left when a participant is created
            user_plan.sessions_left -= 1
            user_plan.save()

@receiver(post_delete, sender=Participants)
def update_sessions_left_on_participant_delete(sender, instance, **kwargs):
    user_plan = instance.user_plan
    if user_plan.plan_pricing.plan.plan_type == 'limited':
        # Decrement sessions_left when a participant is deleted
        user_plan.sessions_left += 1
        user_plan.save()

@receiver(pre_save, sender=Participants)
def capture_previous_assistance_status(sender, instance, **kwargs):
    # Capture the previous assistance status before saving the instance
    if instance.pk:
        original_instance = Participants.objects.get(pk=instance.pk)
        instance._previous_assistance_status = original_instance.assistance_status
    else:
        instance._previous_assistance_status = None

@receiver(post_save, sender=Participants)
def handle_status_change(sender, instance, **kwargs):
    # Check if the status is changed from 'cancelled' to 'registered'
    if instance.user_plan.plan_pricing.plan.plan_type == 'limited':
        if instance.assistance_status == 'registered' and instance._previous_assistance_status == 'cancelled':
            # Increment sessions_left when the status is changed to 'registered'
            instance.user_plan.sessions_left -= 1
            instance.user_plan.save()

        # Check if the status is changed from 'registered' to 'cancelled'
        elif instance.assistance_status == 'cancelled' and instance._previous_assistance_status == 'registered':
            # Decrement sessions_left when the status is changed to 'cancelled'
            instance.user_plan.sessions_left += 1
            instance.user_plan.save()
