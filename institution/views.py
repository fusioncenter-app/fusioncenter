# views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Institution, Site, Space, Staff, Instructor
from custom_user.models import User

from .forms import SiteForm, SpaceForm, StaffForm, InstructorForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def institution_detail(request):
    # Get the logged-in user
    user = request.user

    # If the user is not authenticated, redirect them to the login page
    if not user.is_authenticated:
        return redirect('login')  # Make sure to replace 'login' with your actual login URL

    # If the user is an InstitutionOwner, retrieve their institution directly
    if user.groups.filter(name='InstitutionOwner').exists():
        institution = user.owned_institution
    else:
        # If the user is not an InstitutionOwner, you can handle this case accordingly
        return render(request, 'institution/not_institution_owner.html')

    sites = institution.sites.all().order_by('name')

    context = {
        'institution': institution,
        'sites': sites,
    }

    return render(request, 'institution/institution_detail.html', context)

@login_required(login_url='login')
def create_site(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.institution = request.user.owned_institution  # Assuming you have a reference to the owned institution in your User model
            site.save()
            return redirect('institution_detail')  # Redirect to the institution detail page
    else:
        form = SiteForm()

    return render(request, 'institution/create_site.html', {'form': form})

@login_required(login_url='login')
def edit_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            return redirect('institution_detail')
    else:
        form = SiteForm(instance=site)

    return render(request, 'institution/edit_site.html', {'form': form, 'site': site})

@login_required(login_url='login')
def create_space(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if request.method == 'POST':
        form = SpaceForm(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.site = site
            space.save()
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate
    else:
        form = SpaceForm()

    return render(request, 'institution/create_space.html', {'form': form, 'site': site})

@login_required(login_url='login')
def edit_space(request, space_id):
    space = get_object_or_404(Space, id=space_id)

    if request.method == 'POST':
        form = SpaceForm(request.POST, instance=space)
        if form.is_valid():
            form.save()
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate
    else:
        form = SpaceForm(instance=space)

    return render(request, 'institution/edit_space.html', {'form': form, 'space': space})


# @login_required(login_url='login')
# def staff_list(request):
#     # Get the logged-in user
#     user = request.user

#     # If the user is not authenticated, redirect them to the login page
#     if not user.is_authenticated:
#         return redirect('login')  # Make sure to replace 'login' with your actual login URL

#     # If the user is an InstitutionOwner, retrieve their institution directly
#     if user.groups.filter(name='InstitutionOwner').exists():
#         institution = user.owned_institution
#     else:
#         # If the user is not an InstitutionOwner, you can handle this case accordingly
#         return render(request, 'institution/not_institution_owner.html')

#     staff_members = institution.staff_members.all()

#     context = {
#         'institution': institution,
#         'staff_members': staff_members,
#     }

#     return render(request, 'institution/staff_list.html', context)

# @login_required
# def create_staff(request):
#     template_name = 'your_template_name.html'  # Set your template name

#     if request.method == 'POST':
#         form = StaffForm(request.POST, owner=request.user)

#         if form.is_valid():
#             staff_instance = form.save(commit=False)
#             staff_instance.institution = request.user.institution  # Access the institution directly from the user
#             staff_instance.save()
#             return redirect('success_url')  # Redirect to a success page
#     else:
#         form = StaffForm(owner=request.user)

    

#     return render(request, 'institution/create_staff.html', {'form': form})


# @login_required(login_url='login')
# def edit_staff(request, staff_id):
#     staff = get_object_or_404(Staff, id=staff_id)

#     if request.method == 'POST':
#         form = StaffForm(request.POST, instance=staff)
#         if form.is_valid():
#             form.save()
#             return redirect('staff_list')
#     else:
#         form = StaffForm(instance=staff)

#     return render(request, 'institution/edit_staff.html', {'form': form, 'staff': staff})

# @login_required(login_url='login')
# def delete_staff(request, staff_id):
#     staff = get_object_or_404(Staff, id=staff_id)
    
#     if request.method == 'POST':
#         staff.delete()
#         return redirect('staff_list')

#     return render(request, 'institution/delete_staff.html', {'staff': staff})

@login_required(login_url='login')
def instructor_list(request):
    user = request.user

    if not user.is_authenticated:
        return redirect('login')

    if user.groups.filter(name='InstitutionOwner').exists():
        institution = user.owned_institution
    else:
        return render(request, 'institution/not_institution_owner.html')

    instructors = institution.instructors.all()

    context = {
        'institution': institution,
        'instructors': instructors,
    }

    return render(request, 'institution/instructor_list.html', context)

@login_required(login_url='login')
def create_instructor(request):
    owner = request.user

    if request.method == 'POST':
        form = InstructorForm(request.POST, owner=owner)

        if form.is_valid():
            email = form.cleaned_data['email']

            # Check if an Instructor instance already exists for the user
            instructor_instance, created = Instructor.objects.get_or_create(user=email)

            # Assign the institution to the instructor based on the owner's institution
            instructor_instance.institutions.add(owner.owned_institution)

            # You can perform additional operations if needed before saving
            instructor_instance.save()
            
            return redirect('instructor_list')  # Redirect to the instructor list or wherever appropriate
    else:
        form = InstructorForm(owner=owner)

    return render(request, 'institution/create_instructor.html', {'form': form})

@login_required(login_url='login')
def delete_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)

    if request.method == 'POST':
        # Remove the owner's institution from the instructor's institutions
        owner_institution = request.user.owned_institution
        instructor.institutions.remove(owner_institution)

        return redirect('instructor_list')

    return render(request, 'institution/delete_instructor.html', {'instructor': instructor})

