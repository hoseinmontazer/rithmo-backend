from django.contrib import admin
from .models import Notification, PartnerMessage, PushNotificationToken, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']


@admin.register(PartnerMessage)
class PartnerMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'message']
    readonly_fields = ['created_at', 'read_at']


@admin.register(PushNotificationToken)
class PushNotificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active']
    search_fields = ['user__username', 'token']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_period_reminder', 'push_period_reminder', 'reminder_days_before']
    search_fields = ['user__username']
