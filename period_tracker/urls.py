from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/auth/', include('djoser.urls')),  # Djoser user management URLs
    path('api/auth/jwt/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWT token obtain
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWT token refresh
    path('api/user/', include('user_profile.urls')),  # Include user profile API
    path('api/', include('cycle_tracker.urls')),  # Period tracking URLs
    path('api/ai/', include('ml_suggestions.urls')),  # AI health suggestion URLs
    path('api/notifications/', include('notifications.urls')),  # Notifications & messaging URLs
    path('api/medications/', include('medications.urls')),
    path('api/dashboard/', include('dashboard.urls')),
]
