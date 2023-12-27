#institution.models

from django.db import models
from custom_user.models import User

class Institution(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_institution')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    instagram_username = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='staff_members')
    status = models.CharField(max_length=10, choices=Institution.STATUS_CHOICES, default='active')
    responsible_sites = models.ManyToManyField('Site', related_name='responsible_staff', blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.institution.name}"

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    institutions = models.ManyToManyField(Institution, related_name='instructors')

    def __str__(self):
        return f"{self.user.email} - {', '.join(str(inst) for inst in self.institutions.all())}"


class Site(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.institution.name}"

class Space(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='spaces')
    name = models.CharField(max_length=255)
    max_capacity = models.PositiveIntegerField(default=1)  # Set a default value greater than 0

    def __str__(self):
        return self.name
