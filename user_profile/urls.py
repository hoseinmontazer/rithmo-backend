from django.urls import path
from .views import UserProfileView, UserInvitationView, RemovePartherView

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name="user-profile"),
    path('invitation/', UserInvitationView.as_view(), name="user-invitation"),
    path('partner/remove/',RemovePartherView.as_view(),name="remove-partner")
]
