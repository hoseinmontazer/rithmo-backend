from django.urls import path
from . import views

urlpatterns = [
    path('wellness/', views.WellnessDashboardView.as_view() , name='wellness-dashboard'),
    path('comparison/', views.WellnessComparisonView.as_view(), name='wellness-comparison'),
    path('correlations/', views.WellnessCorrelationsView.as_view(), name='wellness-correlations'),
    
    # Existing wellness log endpoints
    # path('wellness-logs/', views.WellnessLogListCreateView.as_view(), name='wellness-log-list'),
    # path('wellness-logs/<int:pk>/', views.WellnessLogDetailView.as_view(), name='wellness-log-detail'),
]
