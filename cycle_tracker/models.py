from datetime import timedelta, time as datetime_time
from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers
from statistics import stdev
from user_profile.models import UserProfile

class Period(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='periods')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Allow auto-calculation
    predicted_end_date = models.DateField(null=True, blank=True) 
    symptoms = models.TextField(blank=True)  # Track symptoms (cramps, mood, etc.)
    medication = models.TextField(blank=True)  # Track any medication taken
    cycle_length = models.IntegerField(default=28)
    period_duration = models.IntegerField(default=5)
    next_period_start_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']  # Show latest period first

    def __str__(self):
        return f"{self.user.username}'s period from {self.start_date} to {self.end_date if self.end_date else 'ongoing'}"


    def calculate_predicted_end_date(self):
        """Predict the end date based on the user's usual period duration."""
        return self.start_date + timedelta(days=self.user.userprofile.period_duration)




    def update_user_profile(self):
        """Update the user's period duration & cycle length based on recorded fields in Period table."""
        past_periods = Period.objects.filter(user=self.user).order_by('-start_date')[:6]

        if past_periods:
            durations = [p.period_duration for p in past_periods if p.period_duration]
            if durations:
                avg_duration = round(sum(durations) / len(durations))
                self.user.userprofile.period_duration = avg_duration

            cycles = [p.cycle_length for p in past_periods if p.cycle_length]
            if cycles:
                avg_cycle_length = round(sum(cycles) / len(cycles))
                self.user.userprofile.cycle_length = avg_cycle_length

            self.user.userprofile.save()



    def save(self, *args, **kwargs):
        # Check if user is female before allowing period creation
        try:
            profile = self.user.userprofile
            user_gender = profile.sex or 'none'
            
            if user_gender != 'female':
                from django.core.exceptions import ValidationError
                raise ValidationError("Period tracking is only available for female users.")
        except Exception as e:
            if "Period tracking is only available" in str(e):
                raise
            # If profile doesn't exist, allow save (will be caught elsewhere)
            pass

        profile = self.user.userprofile

        # if start and end date is available
        if self.start_date and self.end_date:
            self.period_duration = (self.end_date - self.start_date).days
        
        # if last period is available calc cycle_length
        last_period = (
            Period.objects.filter(user=self.user)
            .exclude(id=self.id)
            .order_by('-start_date')
            .first()
        )

        if last_period and self.start_date:
            self.cycle_length = (self.start_date - last_period.start_date).days

        # predicted_end_date calc
        duration = self.period_duration or profile.period_duration

        if duration and self.start_date:
            self.predicted_end_date = self.start_date + timedelta(days=duration)

        # Smart next_period_start_date calculation
        self.next_period_start_date = self.calculate_smart_next_period()

        super().save(*args, **kwargs)

        self.update_user_profile()

    def calculate_smart_next_period(self):
        """
        Smart calculation for next period start date.
        Uses average cycle length if user has 3+ periods, otherwise uses profile default.
        """
        if not self.start_date:
            return None
            
        # Get user's recent periods (excluding current one being saved)
        recent_periods = Period.objects.filter(user=self.user).exclude(id=self.id).order_by('-start_date')[:6]
        
        # If user has 3+ periods, use average cycle length
        if recent_periods.count() >= 3:
            cycle_lengths = []
            for i, period in enumerate(recent_periods):
                if i < recent_periods.count() - 1:
                    next_period = recent_periods[i + 1]
                    cycle_length = (period.start_date - next_period.start_date).days
                    # Only include reasonable cycle lengths (21-45 days)
                    if 21 <= cycle_length <= 45:
                        cycle_lengths.append(cycle_length)
            
            if cycle_lengths:
                # Use average of recent cycles
                avg_cycle = sum(cycle_lengths) / len(cycle_lengths)
                # Round to nearest day
                smart_cycle = round(avg_cycle)
                return self.start_date + timedelta(days=smart_cycle)
        
        # Fallback to individual cycle length or profile default
        cycle = self.cycle_length or self.user.userprofile.cycle_length
        # Ensure cycle length is reasonable
        if cycle and 21 <= cycle <= 45:
            return self.start_date + timedelta(days=cycle)
        else:
            # Use default 28 days if cycle length is unreasonable
            return self.start_date + timedelta(days=28)

    def calculate_next_period(self):
        """
        Return the predicted start date of the next period.
        Fallback to next_period_start_date if available.
        """
        if self.next_period_start_date:
            return self.next_period_start_date
        elif self.start_date and self.cycle_length:
            return self.start_date + timedelta(days=self.cycle_length)
        else:
            return None


    def analyze_cycle_regularity(self):
        """Analyze cycle regularity based on past periods."""
        past_periods = Period.objects.filter(user=self.user).order_by('-start_date')[:6]

        if len(past_periods) < 2:
            return {
                'average_cycle': None,
                'regularity_score': None,
                'cycle_variations': [],
                'prediction_reliability': None,
                'next_predicted_date': self.next_period_start_date or self.calculate_smart_next_period()
            }

        cycle_lengths = [
            (past_periods[i].start_date - past_periods[i+1].start_date).days
            for i in range(len(past_periods) - 1)
        ]
        avg_cycle = sum(cycle_lengths) / len(cycle_lengths)

        try:
            # Calculate standard deviation and handle edge cases
            cycle_std = stdev(cycle_lengths) if len(set(cycle_lengths)) > 1 else 0  # Prevent exception

            # Debugging: Log the standard deviation
            print(f"Cycle Lengths: {cycle_lengths}")
            print(f"Standard Deviation: {cycle_std}")

            # Adjust regularity score based on cycle variation
            if cycle_std == 0:
                # If no variation, set regularity score to 100
                regularity = 100
            elif cycle_std <= 1:  # Small variations, still regular
                # If the standard deviation is very small, give a high regularity score
                regularity = 90 + (cycle_std * 10)  # Scale slightly based on deviation
            else:
                # Regular case, calculate based on deviation
                regularity = max(0, min(100, 100 - (cycle_std / avg_cycle * 100)))

            # Calculate cycle variations (the difference from the expected cycle)
            variations = []
            expected_date = past_periods[0].start_date
            for period in past_periods:
                diff = abs((expected_date - period.start_date).days)
                variations.append(diff)
                expected_date = period.start_date - timedelta(days=avg_cycle)

            # Calculate prediction reliability based on the regularity of the cycles
            reliability = regularity * (min(len(past_periods), 6) / 6)

            return {
                'average_cycle': round(avg_cycle, 1),
                'regularity_score': round(regularity, 1),
                'cycle_variations': variations,
                'prediction_reliability': round(reliability, 1),
                'next_predicted_date': self.next_period_start_date or self.calculate_smart_next_period()
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                'average_cycle': round(avg_cycle, 1),
                'regularity_score': 0,
                'cycle_variations': [],
                'prediction_reliability': 0,
                'next_predicted_date': self.next_period_start_date or self.calculate_smart_next_period()
            }


            
class Ovulation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ovulations')
    period = models.OneToOneField(Period, on_delete=models.CASCADE)  # One ovulation per period

    class Meta:
        ordering = ['-period__start_date']  # Show latest ovulation first

    def __str__(self):
        return f"Ovulation for {self.user.username} on {self.predict_ovulation()['ovulation_date']}"

    def predict_ovulation(self):
        """
        Predict ovulation and fertile window:
        - Ovulation occurs 14 days before the next period.
        - Fertile window is 5 days before and 1 day after ovulation.
        """
        next_period_start = self.period.next_period_start_date or self.period.calculate_next_period()
        ovulation_date = next_period_start - timedelta(days=14)
        fertile_window_start = ovulation_date - timedelta(days=5)
        fertile_window_end = ovulation_date + timedelta(days=0)
        
        return {
            'ovulation_date': ovulation_date,
            'fertile_window_start': fertile_window_start,
            'fertile_window_end': fertile_window_end
        }


class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="partner_user")
    partner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="linked_partner")

    class Meta:
        unique_together = ('user', 'partner')  # Ensure unique partner relationships

    def __str__(self):
        return f"Partner connection: {self.user.username} ↔ {self.partner.username}"

    def save(self, *args, **kwargs):
        """Prevent self-partnering and duplicate relationships."""
        if self.user == self.partner:
            raise ValueError("A user cannot be their own partner.")
        super().save(*args, **kwargs)

    def get_shared_data(self):
        """Retrieve period and ovulation data for shared tracking."""
        return {
            'periods': list(self.user.periods.values('start_date', 'end_date', 'cycle_length', 'period_duration')),
            'ovulation': list(self.user.ovulations.values('period__start_date', 'period__end_date')),
        }

# Notification models moved to notifications app
# Import them if needed: from notifications.models import Notification, NotificationPreference


class Reminder(models.Model):
    REMINDER_TYPES = [
        ('PERIOD_START', 'Upcoming Period'),
        ('OVULATION', 'Ovulation Alert'),
        ('MEDICATION', 'Medication Reminder'),
        ('CUSTOM', 'Custom Reminder'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES, default='CUSTOM')
    reminder_time = models.DateTimeField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['reminder_time']  # Sort reminders by time

    def __str__(self):
        return f"{self.user.username} - {self.get_reminder_type_display()} at {self.reminder_time}"


class WellnessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wellness_logs') 
    date = models.DateField(auto_now_add=True) 

    # (Basic)
    stress_level = models.IntegerField(default=0)  
    sleep_hours = models.FloatField(default=0)      

    #  (General Health)
    mood_level = models.IntegerField(default=0)    
    energy_level = models.IntegerField(default=5) 
    pain_level = models.IntegerField(default=0)    

    #  (Lifestyle)
    exercise_minutes = models.IntegerField(default=0) 
    nutrition_quality = models.IntegerField(default=3)  
    caffeine_intake = models.IntegerField(default=0)    
    alcohol_intake = models.IntegerField(default=0)     
    smoking = models.IntegerField(default=0)             

    #  (Mental Health)
    anxiety_level = models.IntegerField(default=0) 
    focus_level = models.IntegerField(default=0) 

    notes = models.TextField(blank=True, null=True) 

    class Meta:
        unique_together = ("user", "date")  # Ensures that each user can only have one wellness log entry per day.
