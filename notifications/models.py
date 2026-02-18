from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Notification(models.Model):
    """System notifications for users"""
    NOTIFICATION_TYPES = [
        ('period_reminder', 'Period Reminder'),
        ('period_approaching', 'Period Approaching'),
        ('ovulation', 'Ovulation'),
        ('fertile_window', 'Fertile Window'),
        ('pms_warning', 'PMS Warning'),
        ('wellness_reminder', 'Wellness Log Reminder'),
        ('partner_message', 'Partner Message'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional: Link to related objects
    related_id = models.IntegerField(null=True, blank=True, help_text="ID of related object (period, message, etc)")
    related_type = models.CharField(max_length=50, null=True, blank=True, help_text="Type of related object")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class PartnerMessage(models.Model):
    """Messages between partners"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_partner_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_partner_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class PushNotificationToken(models.Model):
    """Store push notification tokens for mobile devices"""
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    token = models.CharField(max_length=500, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'token']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.device_type} token for {self.user.username}"


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notifications
    email_period_reminder = models.BooleanField(default=True)
    email_ovulation = models.BooleanField(default=True)
    email_partner_message = models.BooleanField(default=True)
    email_wellness_reminder = models.BooleanField(default=False)
    
    # Push notifications
    push_period_reminder = models.BooleanField(default=True)
    push_ovulation = models.BooleanField(default=True)
    push_partner_message = models.BooleanField(default=True)
    push_wellness_reminder = models.BooleanField(default=False)
    
    # In-app notifications
    inapp_period_reminder = models.BooleanField(default=True)
    inapp_ovulation = models.BooleanField(default=True)
    inapp_partner_message = models.BooleanField(default=True)
    inapp_wellness_reminder = models.BooleanField(default=True)
    
    # Timing preferences
    reminder_days_before = models.IntegerField(default=2, help_text="Days before period to send reminder")
    reminder_time = models.TimeField(default='09:00:00', help_text="Preferred time for reminders")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
