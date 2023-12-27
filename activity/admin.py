from django.contrib import admin
from .models import Activity, Session, Participants

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'site', 'custom_capacity', 'instructor')
    list_filter = ('type', 'status', 'site', 'instructor')
    search_fields = ('name', 'description', 'instructor__user__email')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('activity', 'status', 'date', 'from_time', 'to_time', 'space', 'session_capacity')
    list_filter = ('status', 'space')
    search_fields = ('activity__name', 'space__name')

@admin.register(Participants)
class ParticipantsAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'inscription_datetime', 'assistance_datetime', 'assistance_status')
    list_filter = ('assistance_status',)
    search_fields = ('user__email', 'session__activity__name')
