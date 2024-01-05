# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test


from .models import Institution, Site, Space, Staff, Instructor
from .forms import SiteForm, SpaceForm, StaffForm,EditStaffForm, InstructorForm
from custom_user.models import User
from .utils.permissions_utils import is_institution_owner, is_institution_instructor, is_institution_staff, is_owner_of_site, is_staff_responsible_for_site, is_owner_of_space, is_staff_responsible_for_space
from django.contrib import messages

from django.contrib.auth.models import Group

### INSTITUTION

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

### SITE

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
            messages.success(request, 'Site created successfully.')
            return redirect('institution_detail')  # Redirect to the institution detail page

        messages.error(request, 'Error creating the site. Please check the form.')
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
            messages.error(request, 'You do not have permission to edit this site.')
            return render(request, 'permission_denied.html')

        form = self.form_class(instance=site)
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)

        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            messages.error(request, 'You do not have permission to edit this site.')
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site updated successfully.')
            return redirect('institution_detail')

        messages.error(request, 'Error updating the site. Please check the form.')
        return render(request, self.template_name, {'form': form, 'site': site})

### SPACE

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
            messages.error(request, 'You do not have permission to create a space for this site.')
            return render(request, 'permission_denied.html')

        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id, *args, **kwargs):
        site = get_object_or_404(Site, id=site_id)
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            messages.error(request, 'You do not have permission to create a space for this site.')
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.site = site
            space.save()
            messages.success(request, 'Space created successfully.')
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate

        messages.error(request, 'Error creating the space. Please check the form.')
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
            messages.error(request, 'You do not have permission to edit this space.')
            return render(request, 'permission_denied.html')

        form = self.form_class(instance=space)
        return render(request, self.template_name, {'form': form, 'space': space})

    def post(self, request, space_id, *args, **kwargs):
        space = get_object_or_404(Space, id=space_id)
        
        # Check if the user is the owner or a staff member responsible for the space
        if not (is_owner_of_space(request.user, space) or is_staff_responsible_for_space(request.user, space)):
            messages.error(request, 'You do not have permission to edit this space.')
            return render(request, 'permission_denied.html')

        form = self.form_class(request.POST, instance=space)
        if form.is_valid():
            form.save()
            messages.success(request, 'Space updated successfully.')
            return redirect('institution_detail')  # Redirect to the institution detail page or wherever appropriate

        messages.error(request, 'There was an error updating the space.')
        return render(request, self.template_name, {'form': form, 'space': space})


### STAFF

class StaffListView(View):

    template_name = 'institution/staff/staff_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        # Get the logged-in user
        user = request.user

        institution = user.owned_institution

        staff_members = institution.staff_members.all()

        context = {
            'institution': institution,
            'staff_members': staff_members,
        }

        return render(request, self.template_name, context)


class CreateStaffView(View):

    template_name = 'institution/staff/create_staff.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        form = StaffForm(owner=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = StaffForm(request.POST, owner=request.user)

        if form.is_valid():
            try:
                # Get the user with the provided email or return a 404 if not found
                user = User.objects.get(email=form.cleaned_data['email'])
            except User.DoesNotExist:
                form.add_error('email', f"No user found with this email")
                return render(request, self.template_name, {'form': form})

            # Set the user and institution fields of the staff instance
            staff_instance = form.save(commit=False)
            staff_instance.user = user
            staff_instance.institution = request.user.owned_institution
            staff_instance.save()

            # Associate selected responsible sites with the staff instance
            staff_instance.responsible_sites.set(form.cleaned_data['responsible_sites'])

            return redirect('staff_list')  # Redirect to a success page

        return render(request, self.template_name, {'form': form})

class EditStaffView(View):

    template_name = 'institution/staff/edit_staff.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u), login_url='login')(view))

    def get(self, request, staff_id, *args, **kwargs):
        
        staff = get_object_or_404(Staff, id=staff_id)
        form = EditStaffForm(instance=staff,owner=request.user)
        return render(request, self.template_name, {'form': form, 'staff': staff})

    def post(self, request, staff_id, *args, **kwargs):

        staff = get_object_or_404(Staff, id=staff_id)
        form = EditStaffForm(request.POST, instance=staff, owner=request.user)

        if form.is_valid():
            form.save()
            return redirect('staff_list')

        return render(request, self.template_name, {'form': form, 'staff': staff})


class DeleteStaffView(View):
    template_name = 'institution/staff/delete_staff.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u), login_url='login')(view))

    def get(self, request, staff_id, *args, **kwargs):
        staff = get_object_or_404(Staff, id=staff_id)
        return render(request, self.template_name, {'staff': staff})

    def post(self, request, staff_id, *args, **kwargs):
        staff = get_object_or_404(Staff, id=staff_id)

        # Remove user from 'InstitutionStaff' group
        institution_staff_group = Group.objects.get(name='InstitutionStaff')
        staff.user.groups.remove(institution_staff_group)

        staff.delete()
        return redirect('staff_list')



### INSTRUCTOR

class InstructorListView(View):
    template_name = 'institution/instructor/instructor_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.groups.filter(name='InstitutionOwner').exists():
            institution = user.owned_institution
            instructors = institution.instructors.all()
        elif user.groups.filter(name='InstitutionStaff').exists():
            staff_profile = Staff.objects.get(user=user)
            institution = staff_profile.institution
            instructors = institution.instructors.all()
        else:
            return render(request, 'permission_denied.html')

        context = {
            'institution': institution,
            'instructors': instructors,
        }

        return render(request, self.template_name, context)
    
class CreateInstructorView(View):

    template_name = 'institution/instructor/create_instructor.html'
    form_class = InstructorForm

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        owner = request.user
        form = self.form_class(owner=owner)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        owner = request.user
        form = self.form_class(request.POST, owner=owner)

        if form.is_valid():
            email = form.cleaned_data['email']

            # Check if an Instructor instance already exists for the user
            instructor_instance, created = Instructor.objects.get_or_create(user=email)

            # Assign the institution to the instructor based on the user's institution
            if is_institution_owner(owner) and hasattr(owner, 'owned_institution'):
                instructor_instance.institutions.add(owner.owned_institution)
            elif is_institution_staff(owner) and hasattr(owner, 'staff_profile'):
                instructor_instance.institutions.add(owner.staff_profile.institution)

            # You can perform additional operations if needed before saving
            instructor_instance.save()
            
            messages.success(request, 'Instructor added successfully.')
            return redirect('instructor_list')  # Redirect to the instructor list or wherever appropriate

        return render(request, self.template_name, {'form': form})

class DeleteInstructorView(View):
    template_name = 'institution/instructor/delete_instructor.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, instructor_id, *args, **kwargs):
        instructor = get_object_or_404(Instructor, id=instructor_id)
        return render(request, self.template_name, {'instructor': instructor})

    def post(self, request, instructor_id, *args, **kwargs):
        instructor = get_object_or_404(Instructor, id=instructor_id)

        # Check if the user is an owner or staff and has an owned_institution attribute
        if is_institution_owner(request.user) and hasattr(request.user, 'owned_institution'):
            owner_institution = request.user.owned_institution
            instructor.institutions.remove(owner_institution)
            messages.success(request, 'Instructor removed successfully.')
        elif is_institution_staff(request.user) and hasattr(request.user, 'staff_profile'):
            staff_institution = request.user.staff_profile.institution
            instructor.institutions.remove(staff_institution)
            messages.success(request, 'Instructor removed successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this instructor.')

        return redirect('instructor_list')


