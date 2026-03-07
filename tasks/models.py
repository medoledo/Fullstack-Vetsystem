from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from clinics.models import Clinic

class Task(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    deadline = models.DateTimeField(blank=True, null=True)
    is_done = models.BooleanField(default=False)
    done_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')

    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        if self.deadline and not self.is_done:
            return timezone.now() > self.deadline
        return False
