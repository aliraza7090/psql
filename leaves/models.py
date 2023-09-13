from django.db import models

from accounts.models import User

# Create your models here.

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("declined", "Declined"),
    ("withdrawn", "Withdrawn"),
)

LEAVE_TYPE_CHOICES = (
    ("casual", "Casual"),
    ("sick", "Sick"),
    ("annual", "Annual"),
    ("unpaid", "Unpaid"),
)


class Leave(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False, blank=False, related_name="leaves"
    )
    description = (
        models.TextField()
    )  # By default, Django will allow null and blank values in a TextField.
    startDate = models.DateField(
        auto_now_add=False, null=True, blank=True
    )  # By default, Django allows null values for CharField, but it does not allow blank strings unless the blank attribute is set to True.
    endDate = models.DateField(auto_now_add=False, null=True, blank=True)
    days = models.FloatField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, blank=True, null=True, default="pending"
    )
    leaveType = models.CharField(
        max_length=10,
        choices=LEAVE_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    isHalf = models.BooleanField(default=False)
    updatedBy = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    updatedAt = models.DateTimeField(auto_now_add=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_title()} ({self.startDate.strftime('%d/%m/%Y')})"


class LeaveStatistic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=False)
    annualAllowed = models.FloatField(
        default=0.0
    )  # By default, Django will allow null and blank values in a FloatField.
    annualUtilized = models.FloatField(default=0.0)
    casualAllowed = models.FloatField(default=0.0)
    casualUtilized = models.FloatField(default=0.0)
    sickAllowed = models.FloatField(default=0.0)
    sickUtilized = models.FloatField(default=0.0)
    unpaidUtilized = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_title()
