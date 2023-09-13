from django.db import models

# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=255)
    hubStaffId = models.IntegerField(blank=True, null=True)
    avazaId = models.IntegerField(blank=True, null=True)
    isActive = models.BooleanField(default=True, null=True)
    users = models.TextField(blank=True)

    def __str__(self):
        return self.name
