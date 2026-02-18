import random

def get_health_labels(
        gender,
        days_to_next_period,
        current_day_in_cycle, ov_day,
        fertile_start,
        fertile_end,
        cycle_length,
        period_duration,
        num_symptoms,
        stress_level,
        sleep_hours,
        num_medication,
        pain_level,
        anxiety_level,
        mood_level,
        energy_level,
        nutrition_score=5,
        hydration=5
        ):

    primary_label = None

    # ------------------ FEMALE SPECIFIC LOGIC ------------------
    if gender == "female":
        # Period / PMS / Ovulation
        if days_to_next_period == 0 and pain_level >= 7:
            primary_label = "Period today with severe pain: consult doctor"
        elif days_to_next_period == 0 and sleep_hours < 6:
            primary_label = "Period today + poor sleep: prioritize rest & hydration"
        elif days_to_next_period == 0:
            primary_label = "Period today: rest, hydration, iron-rich foods"

        elif 1 <= days_to_next_period <= 2 and stress_level >= 3:
            primary_label = "Upcoming period with stress: relaxation recommended"
        elif 1 <= days_to_next_period <= 2 and energy_level <= 3:
            primary_label = "Upcoming period with low energy: gentle routine"
        elif 1 <= days_to_next_period <= 4 and (pain_level >= 4 or anxiety_level >= 3):
            primary_label = "PMS symptoms: comfort, herbal tea, relaxation"
        elif 1 <= days_to_next_period <= 4:
            primary_label = "Pre-period phase: prepare body with self-care"

        elif current_day_in_cycle == ov_day:
            primary_label = "Ovulation day: high fertility, track symptoms"
        elif fertile_start <= current_day_in_cycle <= fertile_end:
            primary_label = "Fertile window: prioritize reproductive health"

        # Female cycle irregularities
        if primary_label is None:
            if cycle_length < 23:
                primary_label = "Unusually short cycle: monitor irregularities"
            elif cycle_length > 40:
                primary_label = "Unusually long cycle: consult if persistent"
            elif period_duration > 7:
                primary_label = "Prolonged period: consult doctor"

    # ------------------ MALE SPECIFIC LOGIC ------------------
    elif gender == "male":
        if num_symptoms >= 4 and stress_level >= 4:
            primary_label = "Severe stress and multiple symptoms: rest & consult"
        elif num_symptoms >= 4:
            primary_label = "Multiple symptoms: consider rest & hydration"
        elif stress_level >= 4:
            primary_label = "High stress: physical activity or mindfulness"
        elif sleep_hours < 6:
            primary_label = "Poor sleep detected: improve rest tonight"

    # ------------------ UNIVERSAL HEALTH CONDITIONS ------------------
    if primary_label is None:
        # Sleep logic
        if sleep_hours < 4:
            primary_label = "Severe sleep deprivation: urgent rest needed"
        elif 4 <= sleep_hours < 5:
            primary_label = "Very poor sleep: short nap & avoid caffeine"
        elif 5 <= sleep_hours < 6:
            primary_label = "Poor sleep: calming evening routine suggested"
        elif 6 <= sleep_hours < 7:
            primary_label = "Slight sleep deficit: aim for full rest tonight"
        elif 7 <= sleep_hours <= 8:
            primary_label = "Healthy sleep achieved: maintain consistency"
        elif sleep_hours > 9:
            primary_label = "Excessive sleep: ensure balance with activity"

        # Stress logic
        if stress_level == 5:
            primary_label = "Extreme stress: professional help may be required"
        elif stress_level == 4:
            primary_label = "High stress: deep breathing & mindfulness"
        elif stress_level == 3:
            primary_label = "Moderate stress: balance work & rest"
        elif stress_level == 2:
            primary_label = "Mild stress: short walk or music recommended"
        elif stress_level <= 1:
            primary_label = "Low stress: good time for focus & productivity"

        # Energy logic
        if energy_level == 0:
            primary_label = "Exhaustion: urgent rest required"
        elif 1 <= energy_level <= 2:
            primary_label = "Very low energy: naps and proper meals required"
        elif 3 <= energy_level <= 4:
            primary_label = "Low energy: light tasks only"
        elif 5 <= energy_level <= 6:
            primary_label = "Moderate energy: steady pace"
        elif 7 <= energy_level <= 8:
            primary_label = "Good energy: productive activities recommended"
        elif energy_level >= 9:
            primary_label = "Very high energy: ideal time for workout or projects"

        # Nutrition logic
        if nutrition_score <= 2:
            primary_label = "Very poor nutrition: eat balanced meals with protein/veggies"
        elif 3 <= nutrition_score <= 4:
            primary_label = "Poor nutrition: add fruits and fiber"
        elif 5 <= nutrition_score <= 6:
            primary_label = "Average nutrition: maintain and improve"
        elif 7 <= nutrition_score <= 8:
            primary_label = "Good nutrition: balanced intake maintained"
        elif nutrition_score >= 9:
            primary_label = "Excellent nutrition: keep habits strong"

        # Hydration logic
        if hydration <= 2:
            primary_label = "Severe dehydration risk: drink water immediately"
        elif 3 <= hydration <= 4:
            primary_label = "Low hydration: increase water intake today"
        elif 5 <= hydration <= 7:
            primary_label = "Adequate hydration: maintain consistency"
        elif hydration >= 8:
            primary_label = "Excellent hydration: well-balanced intake"

    # ------------------ EMERGENCY OVERRIDES ------------------
    override_label = None
    if sleep_hours < 5 and stress_level >= 4:
        override_label = "Critical: poor sleep + high stress"
    elif pain_level >= 8:
        override_label = "Critical: severe pain, consult doctor"
    elif anxiety_level >= 4:
        override_label = "High anxiety detected: relaxation required"
    elif mood_level <= -1 and energy_level <= 3:
        override_label = "Low mood & low energy: prioritize mental health"
    if override_label:
        primary_label = override_label

    # ------------------ SECONDARY LABELS ------------------
    secondary_labels = []
    if gender == "female":
        if days_to_next_period == 0:
            secondary_labels.append("period_today")
        elif 1 <= days_to_next_period <= 4:
            secondary_labels.append("pms_window")
        if fertile_start <= current_day_in_cycle <= fertile_end:
            secondary_labels.append("fertile_window")
        if current_day_in_cycle == ov_day:
            secondary_labels.append("ovulation_day")

    if num_medication > 0:
        secondary_labels.append("medication_taken")
    if num_symptoms > 0:
        secondary_labels.append("symptoms_present")
    if stress_level >= 3:
        secondary_labels.append("high_stress")
    if sleep_hours < 6:
        secondary_labels.append("sleep_deprivation")
    if energy_level <= 2:
        secondary_labels.append("very_low_energy")
    if hydration <= 3:
        secondary_labels.append("low_hydration")
    if nutrition_score <= 3:
        secondary_labels.append("poor_nutrition")

    # ------------------ FALLBACK IF NO LABEL MATCHED ------------------
    if primary_label is None:
        # Provide a reasonable default based on available data
        if gender == "female":
            if 7 <= sleep_hours <= 8 and stress_level <= 2:
                primary_label = "Healthy routine: maintain balanced lifestyle"
            elif num_symptoms > 0:
                primary_label = "Monitor symptoms: stay hydrated and rest"
            else:
                primary_label = "Normal cycle phase: maintain wellness habits"
        elif gender == "male":
            if 7 <= sleep_hours <= 8 and stress_level <= 2:
                primary_label = "Healthy routine: maintain balanced lifestyle"
            elif num_symptoms > 0:
                primary_label = "Monitor symptoms: stay hydrated and rest"
            else:
                primary_label = "Maintain healthy habits: balanced diet and exercise"
        else:
            primary_label = "Maintain healthy habits: balanced diet and exercise"

    return primary_label, secondary_labels
