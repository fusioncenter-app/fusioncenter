# plans.models

from django.db import models
from activity.models import Activity
from institution.models import Site
from custom_user.models import User

class Plan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('limited', 'Limited'),
        ('unlimited', 'Unlimited'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    activities = models.ManyToManyField(Activity, related_name='plans')

    def __str__(self):
        return self.name

class PlanPricing(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    PRICE_UNIT_CHOICES = [
        ('ARS', 'Argentine Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    name = models.CharField(max_length=255)
    from_date = models.DateField()
    to_date = models.DateField()
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    sessions_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    price_unit = models.CharField(max_length=50, choices=PRICE_UNIT_CHOICES)
    price_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.plan.name} - {self.name}"


class UserPlan(models.Model):

    PAYMENT_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
        ('mercado_pago', 'Mercado Pago'),
        ('paypal', 'PayPal'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_pricing = models.ForeignKey(PlanPricing, on_delete=models.CASCADE)
    sessions_left = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_user_plans')

    def __str__(self):
        return f"{self.user.email} - {self.plan_pricing.plan.name}"
    
    def get_payment_method_display(self):
        return dict(self.PAYMENT_CHOICES).get(self.payment_method, self.payment_method)