from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OvulationDetailView, PeriodViewSet, WellnessLogView, NotificationGeneratorView
)
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'periods', PeriodViewSet, basename='period')
router.register(r'wellness', WellnessLogView, basename='wellnesslog')
# Notifications moved to notifications app - use /api/notifications/ instead

# wellness_router = DefaultRouter()
# wellness_router.register(r'wellness', WellnessLogView, basename='wellnesslog')  # This will create /wellness/ endpoint


urlpatterns = [
    path('', include(router.urls)),
    path('ovulation/', OvulationDetailView.as_view(), name='ovulation-latest'),
    path('ovulation/<int:period_id>/', OvulationDetailView.as_view(), name='ovulation-detail'),
    # notification-preferences moved to /api/notifications/preferences/
    path('generate-notifications/', NotificationGeneratorView.as_view(), name='generate-notifications'),
]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
