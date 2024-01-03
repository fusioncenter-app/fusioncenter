# activity/utils.py

from ..models import Session, Participants
from plans.models import UserPlan
from datetime import timedelta

def should_participate(user, session):
    """
    Implement your logic to determine if the user should participate in the session.
    Return True if the user should participate, False otherwise.
    """
    if user_has_unlimited_plan(user, session):
        return True
    elif user_has_limited_plan(user, session):
        return True
    else:
        return False

def user_has_unlimited_plan(user, session):
    """
    Check if the user has an unlimited pricing plan related to the session's activity.
    """
    unlimited_plans = UserPlan.objects.filter(
        user=user,
        plan_pricing__plan__activities=session.activity,
        plan_pricing__status='active',
        plan_pricing__from_date__lte=session.date,
        plan_pricing__to_date__gte=session.date,
        plan_pricing__plan__plan_type='unlimited'
    )
    
    return unlimited_plans.exists()

def user_has_limited_plan(user, session):
    """
    Check if the user has a limited pricing plan related to the session's activity.
    Also, check if the user is registered for the session with an 'assistance_status' of 'registered'.
    """
    limited_plans = UserPlan.objects.filter(
        user=user,
        plan_pricing__plan__activities=session.activity,
        plan_pricing__status='active',
        plan_pricing__from_date__lte=session.date,
        plan_pricing__to_date__gte=session.date,
        plan_pricing__plan__plan_type='limited'
    )

    is_registered = Participants.objects.filter(
        session=session,
        user=user,
        assistance_status='registered'
    ).exists()

    return limited_plans.exists() and is_registered

def add_participant(user, session, user_plan=None):
    """
    Implement the logic to add the user as a participant in the session.
    """
    # Check if the participant already exists for the user and session
    existing_participant = Participants.objects.filter(session=session, user=user)
    
    if existing_participant.exists():
        pass
    else:
        # Replace this with your logic
        # Use the provided user_plan or fetch it based on the user and session
        if user_plan is None:
            user_plan = UserPlan.objects.get(user=user, plan_pricing__plan__activities=session.activity)
        
        Participants.objects.create(session=session, user=user, assistance_status='registered', user_plan=user_plan)

def remove_participant(participant):
    """
    Implement the logic to remove the participant from the session.
    """
    session = participant.session
    user = participant.user

    # Check if there are other participants for the same session with limited plan pricings
    other_participants_with_limited_plans = Participants.objects.filter(
        session=session,
        user__userplan__plan_pricing__status='active',
        user__userplan__plan_pricing__from_date__lte=session.date,
        user__userplan__plan_pricing__to_date__gte=session.date,
        user__userplan__plan_pricing__plan__plan_type='limited'
    ).exclude(pk=participant.pk)

    if other_participants_with_limited_plans.exists():
        pass
    else:
        # Replace this with your logic to remove the participant
        participant.delete()
