# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test


from .models import Institution, Site, Space, Staff, Instructor
from .forms import SiteForm, SpaceForm, StaffForm, InstructorForm
from custom_user.models import User
from .utils.permissions_utils import is_institution_owner, is_institution_instructor, is_institution_staff, is_owner_of_site, is_staff_responsible_for_site, is_owner_of_space, is_staff_responsible_for_space



class InstitutionDetailView(View):

    template_name = 'institution/institution/institution_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        user = self.request.user

        context = {
            'institution': None,
            'sites': None,
        }

        if user.groups.filter(name='InstitutionOwner').exists():
            # If the user is an InstitutionOwner, retrieve their institution and all sites
            context['institution'] = user.owned_institution
            context['sites'] = user.owned_institution.sites.all().order_by('name')
        elif user.groups.filter(name='InstitutionStaff').exists():
            # If the user is an InstitutionStaff, retrieve the sites they are responsible for
            staff_profile = Staff.objects.get(user=user)
            context['institution'] = staff_profile.institution
            context['sites'] = staff_profile.responsible_sites.all().order_by('name')

        return render(request, self.template_name, context)

class CreateSiteView(View):
    template_name = 'institution/site/create_site.html'
    form_class = SiteForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.institution = request.user.owned_institution  # Assuming you have a reference to the owned institution in your User model
            site.save()
            return redirect('institution_detail')  # Redirect to the institution detail page

        return render(request, self.template_name, {'form': form})

class EditSiteView(View):
    template_name = 'institution/site/edit_site.html'
    form_class = SiteForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = self.form_class(instance=site)
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST, instance=site)
        if form.is_valid():
            form.save()
            return redirect('institution_detail')

        return render(request, self.template_name, {'form': form, 'site': site})




@login_required(login_url='login')
@user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')
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

    return render(request, 'institution/space/create_space.html', {'form': form, 'site': site})

class CreateSpaceView(View):
    template_name = 'institution/space/create_space.html'
    form_class = SpaceForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.site = site
            space.save()
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate

        return render(request, self.template_name, {'form': form, 'site': site})

class EditSpaceView(View):
    template_name = 'institution/space/edit_space.html'
    form_class = SpaceForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, space_id, *args, **kwargs):
        space = get_object_or_404(Space, id=space_id)
        
        # Check if the user is the owner or a staff member responsible for the space
        if not (is_owner_of_space(request.user, space) or is_staff_responsible_for_space(request.user, space)):
            return render(request, 'permission_denied.html')

        form = self.form_class(instance=space)
        return render(request, self.template_name, {'form': form, 'space': space})

    def post(self, request, space_id, *args, **kwargs):
        space = get_object_or_404(Space, id=space_id)
        
        # Check if the user is the owner or a staff member responsible for the space
        if not (is_owner_of_space(request.user, space) or is_staff_responsible_for_space(request.user, space)):
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST, instance=space)
        if form.is_valid():
            form.save()
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate

        return render(request, self.template_name, {'form': form, 'space': space})


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
@user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')
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
@user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')
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
@user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')
def delete_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, id=instructor_id)

    if request.method == 'POST':
        # Remove the owner's institution from the instructor's institutions
        owner_institution = request.user.owned_institution
        instructor.institutions.remove(owner_institution)

        return redirect('instructor_list')

    return render(request, 'institution/delete_instructor.html', {'instructor': instructor})

