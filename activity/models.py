# activity.models
from django.db import models
from institution.models import Instructor, Space, Site
from custom_user.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save


class Activity(models.Model):

    TYPE_CHOICES = [
        ('Ballet', 'Ballet'),
        ('Ballroom', 'Ballroom'),
        ('Belly Dance', 'Belly Dance'),
        ('Breakdance', 'Breakdance'),
        ('Contemporary', 'Contemporary'),
        ('Flamenco', 'Flamenco'),
        ('Folklore','Folklore'),
        ('Hip Hop', 'Hip Hop'),
        ('Jazz', 'Jazz'),
        ('Krumping', 'Krumping'),
        ('Locking', 'Locking'),
        ('Modern Dance', 'Modern Dance'),
        ('Salsa', 'Salsa'),
        ('Street Fusion', 'Street Fusion'),
        ('Swing', 'Swing'),
        ('Tango', 'Tango'),
        ('Tap Dance', 'Tap Dance'),
        ('Vogue', 'Vogue'),
        ('Waacking', 'Waacking'),
        ('Zumba', 'Zumba'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Discipline')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='activities')
    custom_capacity = models.PositiveIntegerField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='instructor_activities')

    def __str__(self):
        return f"{self.name}"

class Session(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('rescheduled', 'Rescheduled'),
        ('pending', 'Pending'),
    ]
    
    DAY_CHOICES = [
        ('1', 'Sunday'),
        ('2', 'Monday'),
        ('3', 'Tuesday'),
        ('4', 'Wednesday'),
        ('5', 'Thursday'),
        ('6', 'Friday'),
        ('7', 'Saturday'),
    ]

    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    date = models.DateField()
    from_time = models.TimeField()
    to_time = models.TimeField()
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='sessions')
    session_capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.activity.name} - {self.date} {self.from_time}"
    
    def save(self, *args, **kwargs):
        """
        Override the save method to update the status of the activity if date, from_time, or to_time is changed.
        """
        if self.pk:
            old_session = Session.objects.get(pk=self.pk)
            if (
                self.date != old_session.date
                or self.from_time != old_session.from_time
                or self.to_time != old_session.to_time
            ):
                self.status = 'rescheduled'
        super().save(*args, **kwargs)

class Participants(models.Model):
    ASSISTANCE_STATUS_CHOICES = [
        ('present', 'Present'),
        ('cancelled', 'Cancelled'),
        ('absent', 'Absent'),
        ('registered', 'Registered'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_plan = models.ForeignKey('plans.UserPlan', on_delete=models.CASCADE, null=True, blank=True)
    inscription_datetime = models.DateTimeField(auto_now_add=True)
    assistance_datetime = models.DateTimeField(null=True, blank=True)
    assistance_editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='editor_assistance_status')
    assistance_status = models.CharField(max_length=20, choices=ASSISTANCE_STATUS_CHOICES, default='registered')

    def __str__(self):
        return f"{self.user.email} - {self.session.activity.name}"
