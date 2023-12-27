# admin.py

from django.contrib import admin
from .models import Institution, Staff, Instructor, Site, Space

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'instagram_username')
    search_fields = ('name', 'owner__email')
    list_filter = ('status',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution')
    search_fields = ('user__email', 'institution__name')

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'display_institutions')

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email'

    def display_institutions(self, obj):
        return ', '.join(str(inst) for inst in obj.institutions.all())

    display_institutions.short_description = 'Institutions'

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'address', 'city', 'country')
    search_fields = ('name', 'institution__name')

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'site', 'max_capacity')
    search_fields = ('name', 'site__name')
    list_filter = ('site',)
