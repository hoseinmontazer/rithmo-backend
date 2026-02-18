from rest_framework import serializers
from .models import Notification, PartnerMessage, PushNotificationToken, NotificationPreference
from django.contrib.auth.models import User


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'read_at',
            'related_id',
            'related_type'
        ]
        read_only_fields = ['created_at', 'read_at']


class PartnerMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PartnerMessage
        fields = [
            'id',
            'sender',
            'sender_username',
            'sender_name',
            'receiver',
            'receiver_username',
            'receiver_name',
            'message',
            'is_read',
            'created_at',
            'read_at'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at', 'read_at']
    
    def get_sender_name(self, obj):
        """Get sender's full name or username"""
        full_name = f"{obj.sender.first_name} {obj.sender.last_name}".strip()
        return full_name if full_name else obj.sender.username
    
    def get_receiver_name(self, obj):
        """Get receiver's full name or username"""
        full_name = f"{obj.receiver.first_name} {obj.receiver.last_name}".strip()
        return full_name if full_name else obj.receiver.username


class PushNotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationToken
        fields = ['id', 'device_type', 'token', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_period_reminder',
            'email_ovulation',
            'email_partner_message',
            'email_wellness_reminder',
            'push_period_reminder',
            'push_ovulation',
            'push_partner_message',
            'push_wellness_reminder',
            'inapp_period_reminder',
            'inapp_ovulation',
            'inapp_partner_message',
            'inapp_wellness_reminder',
            'reminder_days_before',
            'reminder_time',
        ]
