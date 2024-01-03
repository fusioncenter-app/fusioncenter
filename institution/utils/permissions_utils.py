from ..models import Staff

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
    
def is_owner_of_space(user, space):
    # Check if the user is authenticated and has the necessary relationships
    return user.is_authenticated and hasattr(user, 'owned_institution') and user.owned_institution == space.site.institution

def is_staff_responsible_for_space(user, space):
    # Check if the user is a staff member responsible for the given space
    try:
        staff_profile = Staff.objects.get(user=user)
        return space.site in staff_profile.responsible_sites.all()
    except Staff.DoesNotExist:
        return False