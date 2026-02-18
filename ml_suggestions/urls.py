from django.urls import path
from . import views
urlpatterns = [
    path("suggestions/", views.GetSuggetion.get_ai_suggestion, name='ai-suggestion'),
    path("feedback/<int:suggestion_id>/", views.GetSuggetion.give_feedback, name='give-feedback'),
    path('suggestion-history/', views.GetSuggetion.get_suggestion_history, name='suggestion-history'),
    path('model-status/', views.GetSuggetion.get_model_status, name='model-status'),
    path('debug-suggestions/', views.GetSuggetion.debug_suggestions, name='debug-suggestions'),
]
