# your_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserPlan, PlanPricing
from activity.models import Participants
from django.db import transaction
from datetime import date

@receiver(post_save, sender=UserPlan)
def add_participants(sender, instance, created, **kwargs):
    if created:
        # user = get_user_model().objects.get(pk=instance.user_id)
        # plan_pricing = PlanPricing.objects.get(pk=instance.plan_pricing_id)
        # print(f"Created user plan: {instance}")
        # print(f"User: {user}")
        # print(f"Plan Pricing: {plan_pricing}")

        for activity in instance.plan_pricing.plan.activities.all():
            if instance.plan_pricing.plan.plan_type == 'unlimited':
                # Get sessions for the current activity within the plan pricing date range
                sessions = activity.activity_sessions.filter(
                    date__range=(date.today(), instance.plan_pricing.to_date)
                )
                # print(f"Sessions for activity '{activity.name}' in unlimited plan: {sessions}")

                # Check if the user already has a participant instance for the session
                existing_participants = Participants.objects.filter(
                    session__in=sessions,
                    user=instance.user,
                    user_plan__plan_pricing__plan__plan_type='unlimited',
                )

                if not existing_participants.exists():
                    # Use bulk_create for efficiency
                    new_participants = [
                        Participants(session=session, user=instance.user, user_plan=instance)
                        for session in sessions
                    ]

                    with transaction.atomic():
                        Participants.objects.bulk_create(new_participants)
                        # print(f"Created new participants for activity '{activity.name}': {new_participants}")

                        # Delete existing participants for the same sessions
                        existing_participants = Participants.objects.filter(
                            session__in=sessions,
                            user_plan__plan_pricing__plan__plan_type='limited',
                            user=instance.user,
                        )
                        existing_participants.delete()
                        # print(f"Deleted existing participants for activity '{activity.name}': {existing_participants}")
                else:
                    pass
                    # print(f"Participant instances already exist for sessions in activity '{activity.name}'")

