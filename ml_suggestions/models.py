from django.db import models
from cycle_tracker.models import Period
from django.contrib.auth.models import User


class AISuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE, null=True)
    primary_label = models.CharField(max_length=255)
    secondary_labels = models.TextField(blank=True, null=True)
    feedback = models.BooleanField(null=True, blank=True)
    corrected_label = models.CharField(max_length=255, null=True, blank=True)
    response_text = models.TextField(null=True, blank=True)
    model_version = models.CharField(max_length=100, blank=True)
    features = models.TextField(blank=True, null=True)  # ADD THIS FIELD
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Suggestion for {self.user.username} - {self.primary_label}"
