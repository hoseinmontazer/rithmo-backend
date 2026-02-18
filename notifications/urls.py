from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    PartnerMessageViewSet,
    PushTokenViewSet,
    NotificationPreferenceViewSet
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'messages', PartnerMessageViewSet, basename='partner-message')
router.register(r'push-tokens', PushTokenViewSet, basename='push-token')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
]
