from ..views import Staff

def is_institution_owner(user):
    return user.groups.filter(name='InstitutionOwner').exists()

def is_institution_instructor(user):
    return user.groups.filter(name='InstitutionInstructor').exists()

def is_institution_staff(user):
    return user.groups.filter(name='InstitutionStaff').exists()

def is_owner_of_site(user, site):
    # Check if the user is an institution owner and is the owner of the given site
    return user.is_authenticated and hasattr(user, 'owned_institution') and user.owned_institution == site.institution

def is_staff_responsible_for_site(user, site):
    # Check if the user is a staff member responsible for the given site
    try:
        staff_profile = Staff.objects.filter(user=user).first()
        return staff_profile and site in staff_profile.responsible_sites.all()
    except Staff.DoesNotExist:
        return False
    
def is_activity_of_owner_sites(user, activity):
    # Check if the activity is related to the owner's sites
    if is_institution_owner(user):
        owned_sites = user.owned_institution.sites.all()
        return activity.site in owned_sites
    return False

def is_activity_of_staff_sites(user, activity):
    # Check if the activity is related to the staff's responsible sites
    if is_institution_staff(user):
        try:
            staff_profile = Staff.objects.get(user=user)
            return activity.site in staff_profile.responsible_sites.all()
        except Staff.DoesNotExist:
            pass
    return False

def is_session_of_owner_sites(user, session):
    # Check if the session's activity is related to the owner's sites
    if is_institution_owner(user):
        owned_sites = user.owned_institution.sites.all()
        return session.activity.site in owned_sites
    return False

def is_session_of_staff_sites(user, session):
    # Check if the session's activity is related to the staff's responsible sites
    if is_institution_staff(user):
        try:
            staff_profile = Staff.objects.get(user=user)
            return session.activity.site in staff_profile.responsible_sites.all()
        except Staff.DoesNotExist:
            pass
    return False

def is_instructor_of_session(user, session):
    # Check if the user is an instructor of the session
    if is_institution_instructor(user):
        return session.activity.instructor.user == user
    return False

def is_owner_of_space(user, space):
    # Check if the user is an institution owner and is the owner of the given space
    return hasattr(user, 'owned_institution') and space.site.institution == user.owned_institution

def is_staff_responsible_for_space(user, space):
    # Check if the user is a staff member responsible for the given space
    try:
        staff_profile = Staff.objects.get(user=user)
        return staff_profile and space.site in staff_profile.responsible_sites.all()
    except Staff.DoesNotExist:
        return False
