from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.

GENDER_CHOICES = (("male", "Male"), ("female", "Female"), ("other", "Other"))

JOB_TYPE_CHOICES = (
    ("full_time", "Full Time"),
    ("part_time", "Part Time"),
    ("intern", "Intern"),
)


class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(
        max_length=6,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )
    cnic = models.CharField(max_length=17, blank=True, null=True)
    dob = models.DateField(auto_now_add=False, blank=True, null=True)
    joinDate = models.DateField(auto_now_add=False, blank=True, null=True)
    jobType = models.CharField(
        max_length=10,
        choices=JOB_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    skillSet = models.CharField(max_length=255, blank=True, null=True)
    supervisors = models.ManyToManyField("self", blank=True, symmetrical=False)
    isSupervisor = models.BooleanField(default=False)
    isAccountSetup = models.BooleanField(default=False)
    isAnnualAllowed = models.BooleanField(default=False)
    hubStaffPresence = models.BooleanField(default=False)
    avazaPresence = models.BooleanField(default=False)
    hubStaffId = models.CharField(max_length=255, blank=True, null=True)
    avazaId = models.CharField(max_length=255, blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def get_title(self):
        return self.first_name if self.first_name else self.email

    def __str__(self):
        return self.get_title()

    def send_email(self, subject, body):
        send_mail(
            subject=subject,
            message=body,
            from_email="deck.eportal@gmail.com",
            recipient_list=[self.email],
            fail_silently=False,
        )

    def set_password(self, password):
        self.password = make_password(password)

    def is_supervisor_of(self, user):
        return self.id in [supervisor.id for supervisor in user.supervisors.all()]


class HubStaffConfig(models.Model):
    baseUrl = models.CharField(max_length=255)
    organizationId = models.CharField(max_length=255)
    accessToken = models.CharField(max_length=1024, null=True, blank=True)
    refreshToken = models.CharField(max_length=1024)

    class Meta:
        verbose_name_plural = "HubStaff config"

    def save(self, *args, **kwargs):
        self.pk = 1  # set the primary key to 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # prevent deletion of the singleton instance

    @classmethod
    def load(cls):
        try:
            return cls.objects.get(pk=1)
        except ObjectDoesNotExist:
            return None


class AvazaConfig(models.Model):
    baseUrl = models.CharField(max_length=255)
    accessToken = models.CharField(max_length=1024, null=True, blank=True)
    refreshToken = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Avaza config"

    def save(self, *args, **kwargs):
        self.pk = 1  # set the primary key to 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # prevent deletion of the singleton instance

    @classmethod
    def load(cls):
        try:
            return cls.objects.get(pk=1)
        except ObjectDoesNotExist:
            return None
