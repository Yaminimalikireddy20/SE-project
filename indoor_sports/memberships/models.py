from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User

class MembershipPlan(models.Model):
    PLAN_CHOICES = [
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Platinum', 'Platinum'),
    ]

    DURATION_CHOICES = [
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'membership_plan'

    def __str__(self):
        return f"{self.name} - {self.duration} - ${self.price}"


class Membership(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        limit_choices_to={'is_staff': False}  # Ensuring only customers (non-admins) have memberships.
    )

    # ForeignKey to MembershipPlan
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.CASCADE,
        related_name='memberships',  # Optional: This allows you to access memberships related to a plan.
    )

    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Pending', 'Pending'),
        ('Expired', 'Expired'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price for this specific membership instance."
    )

    def __str__(self):
        return f"{self.plan.name} Membership for {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Automatically set expiry status if end_date has passed.
        if self.end_date < timezone.now().date():
            self.status = 'Expired'
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """
        Returns True if the membership has expired.
        """
        return self.end_date < timezone.now().date()
    
    @property
    def remaining_days(self):
        """
        Returns the number of days remaining until expiration (or 0 if expired).
        """
        remaining = (self.end_date - timezone.now().date()).days
        return max(remaining, 0)

    def renew_membership(self):
        """
        Renews the membership by extending the end_date based on the plan.
        """
        if self.plan == 'WEEKLY':
            self.end_date += timedelta(weeks=1)
        elif self.plan == 'MONTHLY':
            self.end_date += timedelta(days=30)
        elif self.plan == 'YEARLY':
            self.end_date += timedelta(days=365)
        self.status = 'Active'
        self.save()




