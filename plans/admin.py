# plans/admin.py

from django.contrib import admin
from .models import Plan, PlanPricing, UserPlan

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'site', 'status')
    search_fields = ('name', 'site__name')  # Adjust the fields based on your needs

@admin.register(PlanPricing)
class PlanPricingAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'from_date', 'to_date', 'sessions_quantity', 'status')
    search_fields = ('name', 'plan__name')  # Adjust the fields based on your needs

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_pricing')
    search_fields = ('user__email', 'plan_pricing__plan__name')  # Adjust the fields based on your needs
