
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicationTypeView,
    MedicationView,
    UserMedicationView,
    UserMedicationLogView,
    MedicationReminderView
)

router = DefaultRouter()
router.register(r'types', MedicationTypeView, basename='types')
router.register(r'drugs', MedicationView, basename='drugs')
router.register(r'my-medications',UserMedicationView,basename='my-medications')
router.register(r'logs',UserMedicationLogView,basename='logs')
router.register(r'reminders',MedicationReminderView,basename='reminders')




urlpatterns = [
    path('', include(router.urls)),
]
