# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Plan, PlanPricing, UserPlan
from institution.models import Institution, Site, Staff
from activity.models import Session, Participants
from .forms import CreatePlanForm, EditPlanForm, CreateUnlimitedPlanPricingForm, CreateLimitedPlanPricingForm, EditLimitedPlanPricingForm, EditUnlimitedPlanPricingForm, AssignUserPlanForm, EditUserPlanForm
from django.http import Http404
from custom_user.models import User
from django.contrib import messages
from django.db import models

from datetime import date

from django.db.models import F,Count,Q
from django.template.loader import render_to_string
from django.http import HttpResponse

from .utils.permissions_utils import (
    is_institution_owner, 
    is_institution_instructor, 
    is_institution_staff, 
    is_owner_of_site, 
    is_staff_responsible_for_site, 
    is_activity_of_owner_sites, 
    is_activity_of_staff_sites,
    is_session_of_owner_sites,
    is_session_of_staff_sites,
    is_owner_of_space,
    is_staff_responsible_for_space,
    is_instructor_of_session,
)

from django.views import View

class PlanListView(View):
    template_name = 'plan/plan_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, *args, **kwargs):
        plans_by_site = {}

        if is_institution_owner(request.user):
            # Get the institution owned by the current user
            institution = Institution.objects.get(owner=request.user)

            # Get the sites related to the institution
            sites = institution.sites.all().order_by('name')

            # Retrieve the plans associated with those sites and order them by site and plan name
            for site in sites:
                plans_by_site[site] = Plan.objects.filter(site=site).order_by('name')
        elif is_institution_staff(request.user):
            # For staff, list plans based on responsible sites
            staff_profile = Staff.objects.get(user=request.user)
            responsible_sites = staff_profile.responsible_sites.all()
            
            for site in responsible_sites:
                plans_by_site[site] = Plan.objects.filter(site=site).order_by('name')

        context = {
            'plans_by_site': plans_by_site,
        }

        # Render the plans in a template
        return render(request, self.template_name, context)
    
class CreatePlanView(View):
    template_name = 'plan/create_plan.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        form = CreatePlanForm(site=site)
        return render(request, self.template_name, {'form': form, 'site': site})

    def post(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        form = CreatePlanForm(request.POST, site=site)

        if form.is_valid():
            plan = form.save(commit=False)
            selected_activity_ids = request.POST.getlist('activities')
            form.set_activities(selected_activity_ids)
            plan.site = site
            form.save()
            return redirect('plan_list')

        return render(request, self.template_name, {'form': form, 'site': site})

class EditPlanView(View):

    template_name = 'plan/edit_plan.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)

        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        form = EditPlanForm(instance=plan, site=site)
        return render(request, self.template_name, {'form': form, 'site': site, 'plan': plan})

    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)

        # Check if the user is the owner
        if not is_institution_owner(request.user):
            return render(request, 'permission_denied.html')

        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        form = EditPlanForm(request.POST, site=site, instance=plan)

        if form.is_valid():
            updated_plan = form.save(commit=False)
            selected_activity_ids = request.POST.getlist('activities')
            form.set_activities(selected_activity_ids)
            updated_plan.site = site
            form.save()
            return redirect('plan_list')

        return render(request, self.template_name, {'form': form, 'site': site, 'plan': plan})
    

class PlanDetailView(View):
    template_name = 'plan/plan_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_id):
        
        plan = get_object_or_404(Plan, id=plan_id)
        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        context = {
            'plan': plan,
        }

        return render(request, self.template_name, context)

class CreatePlanPricingView(View):
    template_name = 'plan/create_plan_pricing.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)

        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        if plan.plan_type == 'unlimited':
            form = CreateUnlimitedPlanPricingForm()
        elif plan.plan_type == 'limited':
            form = CreateLimitedPlanPricingForm()

        context = {
            'form': form,
            'plan': plan,
        }

        return render(request, self.template_name, context)

    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)

        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        if plan.plan_type == 'unlimited':
            form = CreateUnlimitedPlanPricingForm(request.POST)
        elif plan.plan_type == 'limited':
            form = CreateLimitedPlanPricingForm(request.POST)

        if form.is_valid():
            pricing = form.save(commit=False)
            
            # Set status as 'active' directly
            pricing.status = 'active'

            # If the plan is unlimited, exclude sessions_quantity field
            if plan.plan_type == 'unlimited':
                pricing.sessions_quantity = 0

            pricing.plan = plan
            form.save()
            return redirect('plan_detail', plan_id=plan.id)

        context = {
            'form': form,
            'plan': plan,
        }

        return render(request, self.template_name, context)

class EditPlanPricingView(View):
    template_name = 'plan/edit_plan_pricing.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_id, pricing_id):
        plan = get_object_or_404(Plan, id=plan_id)
        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        pricing = get_object_or_404(PlanPricing, id=pricing_id)

        # Check if the user is the owner
        if not is_institution_owner(request.user):
            return render(request, 'permission_denied.html')

        initial_data = {
            'from_date': pricing.from_date.strftime('%Y-%m-%d'),
            'to_date': pricing.to_date.strftime('%Y-%m-%d'),
        }
        
        if plan.plan_type == 'unlimited':
            form = EditUnlimitedPlanPricingForm(instance=pricing, initial=initial_data)
        elif plan.plan_type == 'limited':
            form = EditLimitedPlanPricingForm(instance=pricing, initial=initial_data)

        context = {
            'form': form,
            'plan': plan,
            'pricing': pricing,
        }

        return render(request, self.template_name, context)

    def post(self, request, plan_id, pricing_id):
        plan = get_object_or_404(Plan, id=plan_id)
        site = plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        pricing = get_object_or_404(PlanPricing, id=pricing_id)

        # Check if the user is the owner
        if not is_institution_owner(request.user):
            return render(request, 'permission_denied.html')

        if plan.plan_type == 'unlimited':
            form = EditUnlimitedPlanPricingForm(request.POST, instance=pricing)
        elif plan.plan_type == 'limited':
            form = EditLimitedPlanPricingForm(request.POST, instance=pricing)

        if form.is_valid():
            pricing = form.save(commit=False)
            
            # Set status as 'active' directly
            pricing.status = 'active'

            # If the plan is unlimited, exclude sessions_quantity field
            if plan.plan_type == 'unlimited':
                pricing.sessions_quantity = 0

            pricing.plan = plan
            form.save()
            return redirect('plan_detail', plan_id=plan.id)

        context = {
            'form': form,
            'plan': plan,
            'pricing': pricing,
        }

        return render(request, self.template_name, context)

class PlanPricingDetailView(View):
    template_name = 'plan/plan_pricing_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_pricing_id):
        plan_pricing = get_object_or_404(PlanPricing, id=plan_pricing_id)
        site = plan_pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        context = {
            'plan_pricing': plan_pricing,
            'PAYMENT_CHOICES': UserPlan.PAYMENT_CHOICES
        }

        return render(request, self.template_name, context)


class AssignUserPlanView(View):
    template_name = 'plan/assign_user_plan.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, pricing_id):
        pricing = PlanPricing.objects.get(id=pricing_id)

        site = pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')
        
        form = AssignUserPlanForm()
        return render(request, self.template_name, {'form': form, 'pricing': pricing})

    def post(self, request, pricing_id):
        pricing = PlanPricing.objects.get(id=pricing_id)

        site = pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = AssignUserPlanForm(request.POST, plan_pricing=pricing, created_by=request.user)

        if form.is_valid():
            form.save_user_plan()
            return redirect('plan_pricing_detail', plan_pricing_id=pricing_id)

        return render(request, self.template_name, {'form': form, 'pricing': pricing})
    
class EditUserPlanView(View):
    template_name = 'plan/edit_user_plan.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, user_plan_id):
        user_plan = get_object_or_404(UserPlan, pk=user_plan_id)

        site = user_plan.plan_pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = EditUserPlanForm(instance=user_plan)
        context = {'form': form, 'pricing': user_plan.plan_pricing.id, 'user_plan': user_plan}
        return render(request, self.template_name, context)

    def post(self, request, user_plan_id):
        user_plan = get_object_or_404(UserPlan, pk=user_plan_id)

        site = user_plan.plan_pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        form = EditUserPlanForm(request.POST, instance=user_plan)

        if form.is_valid():
            form.save()
            return redirect('plan_pricing_detail', plan_pricing_id=user_plan.plan_pricing.id)

        context = {'form': form, 'pricing': user_plan.plan_pricing.id, 'user_plan': user_plan}
        return render(request, self.template_name, context)


class PlanPricingSessionListView(View):

    template_name = 'plan/plan_pricing_session_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, plan_pricing_id):
        
        # Get the PlanPricing object
        plan_pricing = get_object_or_404(PlanPricing, id=plan_pricing_id)

        site = plan_pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        # Get the related plan activities
        plan_activities = plan_pricing.plan.activities.all()

        # Get the sessions within the date range of the plan pricing
        sessions = Session.objects.filter(
            activity__in=plan_activities,
            date__range=[plan_pricing.from_date, plan_pricing.to_date]
        ).order_by('date', 'from_time')

        sessions = sessions.order_by('date', 'from_time')

        for session in sessions:
            # Calculate counts for different assistance_status
            session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
            session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
            session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

            # Calculate total_participants and availability
            session.total_participants = session.registered_count + session.present_count + session.absent_count
            session.availability = session.session_capacity - session.total_participants

            # Calculate all_participants_present using Case expression
            if session.registered_count > 0:
                session.all_participants_present = False
            elif session.total_participants == 0:
                session.all_participants_present = None
            else:
                session.all_participants_present = True

        today = date.today()

        context = {
            'plan_pricing': plan_pricing,
            'sessions': sessions,
            'today': today,
        }

        return render(request, self.template_name, context)


class ParticipantPlanPricingSessionListView(View):
    
    template_name = 'plan/participant_plan_pricing_session_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(user_passes_test(lambda u: is_institution_owner(u) or is_institution_staff(u), login_url='login')(view))

    def get(self, request, user_plan_id):
        
        user_plan = get_object_or_404(UserPlan, id=user_plan_id)

        site = user_plan.plan_pricing.plan.site
        # Check if the user is the owner or a staff member responsible for the site
        if not (is_owner_of_site(request.user, site) or is_staff_responsible_for_site(request.user, site)):
            return render(request, 'permission_denied.html')

        today = date.today()

        sessions = Session.objects.filter(
            participants__user=user_plan.user,
            participants__user_plan=user_plan.id
        ).order_by('date', 'from_time')

        for session in sessions:
            # Calculate counts for different assistance_status
            session.registered_count = Participants.objects.filter(session=session, assistance_status='registered').count()
            session.present_count = Participants.objects.filter(session=session, assistance_status='present').count()
            session.absent_count = Participants.objects.filter(session=session, assistance_status='absent').count()

            # Calculate total_participants and availability
            session.total_participants = session.registered_count + session.present_count + session.absent_count
            session.availability = session.session_capacity - session.total_participants

        # Loop through sessions and obtain user's session participants
        for session in sessions:
            participant = Participants.objects.filter(user=user_plan.user, session=session).first()
            if participant:
                session.assistance_status = participant.assistance_status
                session.participant_id = participant.id
                session.session_user_plan_id = participant.user_plan.id

        context = {
            'user_plan': user_plan,
            'sessions': sessions,
            'today': today,
        }

        return render(request, self.template_name, context)



'''

    Participant Views

'''

class ParticipantPlanListView(View):
    template_name = 'participant/plan_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, *args, **kwargs):
        user_plans = UserPlan.objects.filter(user=request.user)

        # Create a dictionary to store plans by site
        plans_by_site = {}

        for user_plan in user_plans:
            site = user_plan.plan_pricing.plan.site

            # If the site is not in the dictionary, create an empty list
            if site not in plans_by_site:
                plans_by_site[site] = []

            # Check if the plan is already added for the site
            plan_already_added = any(
                plan_info['plan_id'] == user_plan.plan_pricing.plan.id for plan_info in plans_by_site[site]
            )

            if not plan_already_added:
                # Get the activities associated with the plan
                activities = user_plan.plan_pricing.plan.activities.all()

                plan_info = {
                    'plan_id': user_plan.plan_pricing.plan.id,
                    'institution_name': site.institution.name,
                    'plan_name': user_plan.plan_pricing.plan.name,
                    'plan_type': user_plan.plan_pricing.plan.plan_type,
                    'status': user_plan.plan_pricing.plan.status,
                    'from_date': user_plan.plan_pricing.from_date,
                    'to_date': user_plan.plan_pricing.to_date,
                    'created_at': user_plan.created_at,
                    'created_by': user_plan.created_by.email if user_plan.created_by else None,
                    'activities': activities,  # Add activities to the plan_info dictionary
                    # Add other plan details as needed
                }

                plans_by_site[site].append(plan_info)

        return render(request, self.template_name, {'plans_by_site': plans_by_site})


class ParticipantPlanDetailView(View):
    
    template_name = 'participant/plan_detail.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, plan_id, *args, **kwargs):
        
        # Get the plan
        plan = get_object_or_404(Plan, id=plan_id)

        # Get all user plans for the specified plan assigned to the user
        user_plans = UserPlan.objects.filter(user=request.user, plan_pricing__plan=plan)

        context = {
            'plan': plan,
            'user_plans': user_plans,
        }

        return render(request, self.template_name, context)


class ParticipantPlanPricingSessionsView(View):

    template_name = 'participant/session_list.html'

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return login_required(login_url='login')(view)

    def get(self, request, user_plan_id, *args, **kwargs):
        # Get the UserPlan object
        user_plan = get_object_or_404(UserPlan, user=request.user, id=user_plan_id)

        # Get the PlanPricing object associated with the UserPlan
        plan_pricing = user_plan.plan_pricing

        # Get the related plan activities
        plan_activities = plan_pricing.plan.activities.all()

        # Get the sessions within the date range of the plan pricing
        sessions = Session.objects.filter(
            activity__in=plan_activities,
            date__range=[plan_pricing.from_date, plan_pricing.to_date]
        ).annotate(
            registered_count=Count('participants', filter=Q(participants__assistance_status='registered')),
            present_count=Count('participants', filter=Q(participants__assistance_status='present')),
            absent_count=Count('participants', filter=Q(participants__assistance_status='absent')),
            total_participants=F('registered_count') + F('present_count') + F('absent_count'),
            availability=F('session_capacity') - F('total_participants')
        ).order_by('date','from_time')

        for session in sessions:
            participant = Participants.objects.filter(user=request.user, session=session).first()
            session.assistance_status = participant.assistance_status if participant else None
            session.session_user_plan_id = participant.user_plan.id if participant else user_plan.id

        context = {
            'plan_pricing': plan_pricing,
            'sessions': sessions,
            'user_plan': user_plan,
            'today': date.today(),
        }

        return render(request, self.template_name, context)




### HTMX



@login_required(login_url='login')
def plan_info_htmx(request, plan_id,):
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Render the updated inner HTML based on the new status
    updated_inner_html = render_to_string('plans/htmx/plan_info.html', {'plan': plan}, request=request)

    return HttpResponse(updated_inner_html)