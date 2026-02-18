from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class MedicationType(models.Model):
    """Types of medications (Pain Relief, Hormonal, Supplements, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI")
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Medication(models.Model):
    """Individual medications/drugs"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    medication_type = models.ForeignKey(MedicationType, on_delete=models.CASCADE, related_name='medications')
    description = models.TextField(blank=True)
    common_dosages = models.JSONField(default=list, help_text="List of common dosages")
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    is_prescription = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'generic_name']

    def __str__(self):
        return f"{self.name} ({self.generic_name})" if self.generic_name else self.name


class UserMedication(models.Model):
    """User's personal medication tracking"""
    FREQUENCY_CHOICES = [
        ('as_needed', 'As Needed'),
        ('daily', 'Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times_daily', 'Three Times Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_medications')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=200, blank=True, help_text="Custom name if not in medication list")
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='as_needed')
    custom_frequency = models.CharField(max_length=200, blank=True, help_text="Custom frequency description")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'medication')
    def __str__(self):
        med_name = self.custom_name or self.medication.name
        return f"{self.user.username} - {med_name} ({self.dosage})"

    @property
    def medication_name(self):
        return self.custom_name or self.medication.name


class MedicationLog(models.Model):
    """Daily medication intake tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medication_logs')
    user_medication = models.ForeignKey(UserMedication, on_delete=models.CASCADE, related_name='logs')
    date_taken = models.DateTimeField()
    dosage_taken = models.CharField(max_length=100)
    effectiveness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rate effectiveness 1-5"
    )
    side_effects_experienced = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_taken']

    def __str__(self):
        return f"{self.user.username} - {self.user_medication.medication_name} on {self.date_taken.date()}"


class MedicationReminder(models.Model):
    """Medication reminders for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medication_reminders')
    user_medication = models.ForeignKey(UserMedication, on_delete=models.CASCADE, related_name='reminders')
    reminder_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    days_of_week = models.JSONField(default=list, help_text="List of weekday numbers (0=Monday, 6=Sunday)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reminder_time']

    def __str__(self):
        return f"{self.user.username} - {self.user_medication.medication_name} at {self.reminder_time}"


class MedicationInteraction(models.Model):
    """Track potential medication interactions"""
    medication1 = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_as_med1')
    medication2 = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_as_med2')
    interaction_type = models.CharField(max_length=50, choices=[
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('severe', 'Severe'),
    ])
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['medication1', 'medication2']

    def __str__(self):
        return f"{self.medication1.name} + {self.medication2.name} ({self.interaction_type})"