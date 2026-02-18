#!/usr/bin/env python
"""
Check what data exists for a user to help debug predictions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'period_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from cycle_tracker.models import Period, WellnessLog
from user_profile.models import UserProfile
import sys

if len(sys.argv) < 2:
    print("Usage: python check_user_data.py <username>")
    print("\nAvailable users:")
    for user in User.objects.all():
        print(f"  - {user.username}")
    exit(1)

username = sys.argv[1]

try:
    user = User.objects.get(username=username)
except User.DoesNotExist:
    print(f"❌ User '{username}' not found")
    exit(1)

print(f"👤 User: {user.username}")
print(f"   ID: {user.id}")

# Check profile
try:
    profile = user.userprofile
    print(f"\n✅ Profile exists:")
    print(f"   Sex: {profile.sex}")
    print(f"   Cycle length: {profile.cycle_length}")
    print(f"   Period duration: {profile.period_duration}")
except UserProfile.DoesNotExist:
    print("\n❌ No profile found")

# Check periods
periods = Period.objects.filter(user=user).order_by('-start_date')
print(f"\n📅 Periods: {periods.count()}")
for i, period in enumerate(periods[:3], 1):
    print(f"   {i}. Start: {period.start_date}, End: {period.end_date}")
    print(f"      Symptoms: {period.symptoms or 'None'}")
    print(f"      Medication: {period.medication or 'None'}")

# Check wellness logs
wellness_logs = WellnessLog.objects.filter(user=user).order_by('-date')
print(f"\n💪 Wellness Logs: {wellness_logs.count()}")
for i, log in enumerate(wellness_logs[:3], 1):
    print(f"   {i}. Date: {log.date}")
    print(f"      Stress: {log.stress_level}, Sleep: {log.sleep_hours}h")
    print(f"      Mood: {log.mood_level}, Energy: {log.energy_level}")
    print(f"      Pain: {log.pain_level}")

# Check AI suggestions
from ml_suggestions.models import AISuggestion
suggestions = AISuggestion.objects.filter(user=user).order_by('-created_at')
print(f"\n🤖 AI Suggestions: {suggestions.count()}")
for i, sug in enumerate(suggestions[:3], 1):
    print(f"   {i}. Label: {sug.primary_label}")
    print(f"      Feedback: {sug.feedback}")
    print(f"      Corrected: {sug.corrected_label or 'N/A'}")
    print(f"      Created: {sug.created_at}")

print("\n" + "="*50)
if wellness_logs.count() == 0:
    print("⚠️  No wellness logs! Add some for better predictions.")
if periods.count() == 0:
    print("⚠️  No periods! Add period data.")
