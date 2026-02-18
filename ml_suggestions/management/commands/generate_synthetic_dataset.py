import random
from datetime import date
import pandas as pd
import os
from django.core.management.base import BaseCommand
from cycle_tracker.models import Period, WellnessLog
from user_profile.models import UserProfile
from ml_suggestions.management.commands.get_health_labels import get_health_labels
from ml_suggestions.management.commands.response import generate_response
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = "Build synthetic + real dataset (Period + UserProfile + WellnessLog)"

    def handle(self, *args, **options):
        rows = []

        # --- 1. Real data from DB ---
        for period in Period.objects.all():
            try:
                profile = period.user.userprofile
            except UserProfile.DoesNotExist:
                continue

            wellness = period.user.wellness_logs.filter(date__lte=period.start_date).order_by('-date').first()
            num_symptoms = len([s for s in (period.symptoms or "").split(",") if s.strip()])
            num_medication = len([m for m in (period.medication or "").split(",") if m.strip()])

            # Current day in cycle
            current_day = 0
            if period.start_date:
                today = date.today()
                end = period.end_date or period.predicted_end_date or period.start_date
                if period.start_date <= today <= end:
                    current_day = (today - period.start_date).days + 1

            days_to_next = 0
            if period.next_period_start_date:
                days_to_next = (period.next_period_start_date - (end or today)).days

            rows.append({
                "user_id": period.user.id,
                "period_id": period.id,
                "gender": profile.sex or "none",
                "cycle_length": period.cycle_length or profile.cycle_length,
                "period_duration": period.period_duration or profile.period_duration,
                "current_day_in_cycle": current_day,
                "num_symptoms": num_symptoms,
                "num_medication": num_medication,
                "days_to_next_period": days_to_next,
                "stress_level": getattr(wellness, "stress_level", getattr(profile, "stress_level", 0)),
                "sleep_hours": getattr(wellness, "sleep_hours", getattr(profile, "sleep_hours", 0)),
                "mood_level": getattr(wellness, "mood_level", 0),
                "energy_level": getattr(wellness, "energy_level", 5),
                "pain_level": getattr(wellness, "pain_level", 0),
                "exercise_minutes": getattr(wellness, "exercise_minutes", 0),
                "nutrition_quality": getattr(wellness, "nutrition_quality", 3),
                "caffeine_intake": getattr(wellness, "caffeine_intake", 0),
                "alcohol_intake": getattr(wellness, "alcohol_intake", 0),
                "smoking": getattr(wellness, "smoking", 0),
                "anxiety_level": getattr(wellness, "anxiety_level", 0),
                "focus_level": getattr(wellness, "focus_level", 0),
                "primary_label": None,
                "secondary_labels": None,
                "response_text": None
            })

        # --- 2. Synthetic data ---
        label_count = int(os.getenv('LABEL_COUNT', 5000))
        for _ in range(label_count):
            gender = random.choice(["male", "female"])
            cycle_length = random.randint(21, 45)
            period_duration = random.randint(3, 10)
            current_day_in_cycle = random.randint(1, cycle_length)
            num_symptoms = random.randint(0, 5)
            num_medication = random.randint(0, 2)
            stress_level = random.randint(0, 5)
            sleep_hours = random.randint(4, 9)
            days_to_next_period = cycle_length - current_day_in_cycle
            mood_level = random.randint(-2, 2)
            energy_level = random.randint(0, 10)
            pain_level = random.randint(0, 10)
            exercise_minutes = random.randint(0, 120)
            nutrition_quality = random.randint(1, 5)
            caffeine_intake = random.randint(0, 5)
            alcohol_intake = random.randint(0, 3)
            smoking = random.randint(0, 20)
            anxiety_level = random.randint(0, 5)
            focus_level = random.randint(0, 10)

            ov_day = cycle_length // 2
            fertile_start = ov_day - 3
            fertile_end = ov_day + 2

            primary_label, secondary_labels = get_health_labels(
                gender=gender,
                days_to_next_period=days_to_next_period,
                current_day_in_cycle=current_day_in_cycle,
                ov_day=ov_day,
                fertile_start=fertile_start,
                fertile_end=fertile_end,
                cycle_length=cycle_length,
                period_duration=period_duration,
                num_symptoms=num_symptoms,
                stress_level=stress_level,
                sleep_hours=sleep_hours,
                num_medication=num_medication,
                pain_level=pain_level,
                anxiety_level=anxiety_level,
                mood_level=mood_level,
                energy_level=energy_level
            )

            rows.append({
                "user_id": None,
                "period_id": None,
                "gender": gender,
                "cycle_length": cycle_length,
                "period_duration": period_duration,
                "current_day_in_cycle": current_day_in_cycle,
                "num_symptoms": num_symptoms,
                "num_medication": num_medication,
                "stress_level": stress_level,
                "sleep_hours": sleep_hours,
                "days_to_next_period": days_to_next_period,
                "mood_level": mood_level,
                "energy_level": energy_level,
                "pain_level": pain_level,
                "exercise_minutes": exercise_minutes,
                "nutrition_quality": nutrition_quality,
                "caffeine_intake": caffeine_intake,
                "alcohol_intake": alcohol_intake,
                "smoking": smoking,
                "anxiety_level": anxiety_level,
                "focus_level": focus_level,
                "primary_label": primary_label,
                "secondary_labels": ";".join(secondary_labels),
                "response_text": generate_response(primary_label)
            })

        df = pd.DataFrame(rows)
        df.to_csv("training_dataset.csv", index=False)
        self.stdout.write(self.style.SUCCESS("✅ Dataset exported to training_dataset.csv"))
