

def is_institution_owner(user):
    return user.groups.filter(name='InstitutionOwner').exists()

def is_institution_instructor(user):
    return user.groups.filter(name='InstitutionInstructor').exists()

def is_institution_staff(user):
    return user.groups.filter(name='InstitutionStaff').exists()