from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Notification, PartnerMessage, PushNotificationToken, NotificationPreference
from .serializers import (
    NotificationSerializer,
    PartnerMessageSerializer,
    PushNotificationTokenSerializer,
    NotificationPreferenceSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        return Response({
            'count': unread.count(),
            'notifications': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'status': 'success',
            'marked_read': updated
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'status': 'success',
            'notification': self.get_serializer(notification).data
        })


class PartnerMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for partner messaging"""
    serializer_class = PartnerMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get messages sent to or from the user"""
        user = self.request.user
        return PartnerMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
    
    def perform_create(self, serializer):
        """Send a message to partner"""
        user = self.request.user
        receiver_id = self.request.data.get('receiver')
        
        # Verify receiver is user's partner
        try:
            user_profile = user.userprofile
            partners = user_profile.partners.all()
            
            if not partners.filter(user_id=receiver_id).exists():
                raise serializers.ValidationError("You can only send messages to your partner")
            
            # Save message
            message = serializer.save(sender=user)
            
            # Create notification for receiver
            Notification.objects.create(
                user_id=receiver_id,
                notification_type='partner_message',
                title='New message from partner',
                message=f"{user.username} sent you a message",
                related_id=message.id,
                related_type='partner_message'
            )
            
        except Exception as e:
            raise serializers.ValidationError(str(e))
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """Get conversation with partner"""
        partner_id = request.query_params.get('partner_id')
        
        if not partner_id:
            return Response(
                {'error': 'partner_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(
            Q(sender=request.user, receiver_id=partner_id) |
            Q(sender_id=partner_id, receiver=request.user)
        ).order_by('created_at')
        
        # Mark received messages as read
        messages.filter(receiver=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        serializer = self.get_serializer(messages, many=True)
        return Response({
            'count': messages.count(),
            'messages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages"""
        unread = self.get_queryset().filter(
            receiver=request.user,
            is_read=False
        )
        serializer = self.get_serializer(unread, many=True)
        return Response({
            'count': unread.count(),
            'messages': serializer.data
        })


class PushTokenViewSet(viewsets.ModelViewSet):
    """ViewSet for managing push notification tokens"""
    serializer_class = PushNotificationTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Register a push notification token"""
        # Deactivate old tokens for this device type
        device_type = self.request.data.get('device_type')
        self.get_queryset().filter(device_type=device_type).update(is_active=False)
        
        # Save new token
        serializer.save(user=self.request.user, is_active=True)


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """ViewSet for notification preferences"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)
    
    def create(self, request):
        """Update notification preferences (POST)"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """Update notification preferences (PUT/PATCH)"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
