# train_ai_model.py
import os
import joblib
import pandas as pd
import numpy as np
from datetime import timedelta
from django.core.management.base import BaseCommand
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from django.conf import settings
from transformers import pipeline
from cycle_tracker.models import Period, WellnessLog
from ml_suggestions.models import AISuggestion
from user_profile.models import UserProfile

# ---------------- Paths ----------------
MODEL_PATH = os.path.join(settings.BASE_DIR, "ml_models")
CACHE_PATH = os.path.join(settings.BASE_DIR, "ml_cache")
os.makedirs(MODEL_PATH, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)

# ---------------- Transformer Pipeline ----------------
rewriter = pipeline(
    "text2text-generation",
    model="google/flan-t5-large",
    device=-1  # CPU
)

# ---------------- Helper Functions ----------------
def generate_health_response(label, features_dict):
    """Generate dynamic, detailed health recommendation based on primary_label and context."""
    if not label or label.lower() == "unknown":
        return "No recommendation available."
    
    # Extract key wellness metrics for context
    stress = features_dict.get('stress_level', 0)
    sleep = features_dict.get('sleep_hours', 7)
    mood = features_dict.get('mood_level', 0)
    energy = features_dict.get('energy_level', 5)
    pain = features_dict.get('pain_level', 0)
    exercise = features_dict.get('exercise_minutes', 0)
    gender = features_dict.get('gender', 2)  # 0=male, 1=female, 2=none
    
    # Determine gender
    is_female = gender == 1
    is_male = gender == 0
    gender_text = "female" if is_female else ("male" if is_male else "person")
    
    # Check if label is gender-inappropriate
    female_keywords = ['period', 'pms', 'ovulation', 'fertile', 'menstrual', 'cycle']
    is_female_specific = any(keyword in label.lower() for keyword in female_keywords)
    
    if is_male and is_female_specific:
        # Male got female-specific label - provide general wellness advice
        return f"Focus on maintaining your overall health with balanced nutrition, regular exercise, and adequate rest. Your current wellness metrics suggest prioritizing stress management and quality sleep."
    
    # Build detailed context
    context_parts = []
    if stress >= 3:
        context_parts.append(f"high stress (level {stress})")
    if sleep < 6:
        context_parts.append(f"poor sleep ({sleep} hours)")
    elif sleep >= 8:
        context_parts.append(f"good sleep ({sleep} hours)")
    if mood < 0:
        context_parts.append("low mood")
    elif mood > 0:
        context_parts.append("positive mood")
    if energy <= 3:
        context_parts.append("low energy")
    elif energy >= 7:
        context_parts.append("high energy")
    if pain >= 5:
        context_parts.append(f"significant pain (level {pain})")
    if exercise > 30:
        context_parts.append(f"active ({exercise} min exercise)")
    
    context_text = ", ".join(context_parts) if context_parts else "normal wellness metrics"
    
    # Gender-specific prompt
    if is_female and is_female_specific:
        prompt = (
            f"You are a compassionate women's health advisor. "
            f"Health situation: {label}. "
            f"User context: {context_text}. "
            f"Provide detailed, empathetic advice for this female health situation. "
            f"Include 2-3 specific suggestions. Be warm and supportive. "
            f"Write 3-4 sentences."
        )
    elif is_male:
        prompt = (
            f"You are a compassionate men's health advisor. "
            f"Health situation: {label}. "
            f"User context: {context_text}. "
            f"Provide detailed, empathetic advice for men's wellness. "
            f"Include 2-3 specific suggestions. Be warm and supportive. "
            f"Write 3-4 sentences."
        )
    else:
        prompt = (
            f"You are a compassionate health and wellness advisor. "
            f"Health situation: {label}. "
            f"User context: {context_text}. "
            f"Provide a detailed, empathetic, and actionable health recommendation. "
            f"Include 2-3 specific suggestions. Be warm and supportive. "
            f"Write 3-4 sentences."
        )
    
    try:
        output = rewriter(prompt, max_new_tokens=200, do_sample=True, top_p=0.92, top_k=50, 
                         temperature=0.8, no_repeat_ngram_size=3)
        text = output[0]['generated_text'].strip()
        return text if text else f"Based on your current situation ({label}), focus on rest, hydration, and balanced nutrition. Listen to your body and adjust your routine as needed."
    except Exception as e:
        # Fallback with context-aware response
        return f"Based on your current situation ({label}) with {context_text}, focus on rest, hydration, and balanced nutrition. Listen to your body and adjust your routine as needed."

def get_recent_wellness_features(user, period_start_date, days=3):
    """Aggregate last N days of WellnessLog before period_start_date."""
    logs = WellnessLog.objects.filter(
        user=user,
        date__lt=period_start_date
    ).order_by('-date')[:days]

    if not logs:
        # Default values if no logs
        return {
            "stress_level": 0,
            "sleep_hours": 7,
            "mood_level": 0,
            "energy_level": 5,
            "pain_level": 0,
            "exercise_minutes": 0,
            "nutrition_quality": 3,
            "caffeine_intake": 0,
            "alcohol_intake": 0,
            "smoking": 0,
            "anxiety_level": 0,
            "focus_level": 0,
            "has_wellness_logs": 0
        }

    # Compute mean for numeric features
    agg = {}
    numeric_fields = [
        "stress_level", "sleep_hours", "mood_level", "energy_level",
        "pain_level", "exercise_minutes", "nutrition_quality", "caffeine_intake",
        "alcohol_intake", "smoking", "anxiety_level", "focus_level"
    ]
    for field in numeric_fields:
        agg[field] = round(np.mean([getattr(log, field, 0) for log in logs]), 2)
    agg["has_wellness_logs"] = 1
    return agg

# ---------------- Command ----------------
class Command(BaseCommand):
    help = "Train AI suggestion model with Period + Feedback + 3-day WellnessLog"

    def handle(self, *args, **options):
        rows = []

        # --- 1. Load synthetic data if available ---
        synthetic_csv = os.path.join(settings.BASE_DIR, "training_dataset.csv")
        if os.path.exists(synthetic_csv):
            self.stdout.write("📂 Loading synthetic training data...")
            synthetic_df = pd.read_csv(synthetic_csv)
            # Convert to rows format
            for _, row in synthetic_df.iterrows():
                if pd.notna(row.get('primary_label')):  # Only include labeled synthetic data
                    rows.append({
                        "user_id": row.get('user_id'),
                        "period_id": row.get('period_id'),
                        "gender": row.get('gender', 'none'),
                        "cycle_length": row.get('cycle_length', 28),
                        "period_duration": row.get('period_duration', 5),
                        "current_day_in_cycle": row.get('current_day_in_cycle', 0),
                        "num_symptoms": row.get('num_symptoms', 0),
                        "num_medication": row.get('num_medication', 0),
                        "days_to_next_period": row.get('days_to_next_period', 0),
                        "stress_level": row.get('stress_level', 0),
                        "sleep_hours": row.get('sleep_hours', 7),
                        "mood_level": row.get('mood_level', 0),
                        "energy_level": row.get('energy_level', 5),
                        "pain_level": row.get('pain_level', 0),
                        "exercise_minutes": row.get('exercise_minutes', 0),
                        "nutrition_quality": row.get('nutrition_quality', 3),
                        "caffeine_intake": row.get('caffeine_intake', 0),
                        "alcohol_intake": row.get('alcohol_intake', 0),
                        "smoking": row.get('smoking', 0),
                        "anxiety_level": row.get('anxiety_level', 0),
                        "focus_level": row.get('focus_level', 0),
                        "has_wellness_logs": 1,  # Synthetic data has wellness info
                        "is_feedback": 0,
                        "primary_label": row.get('primary_label'),
                        "secondary_labels": row.get('secondary_labels'),
                        "response_text": row.get('response_text')
                    })
            self.stdout.write(f"   Loaded {len(rows)} synthetic samples")
        else:
            self.stdout.write("⚠️  No synthetic data found. Using only real data.")

        # --- 2. Collect Period + Wellness + UserProfile data ---
        real_data_start = len(rows)
        for period in Period.objects.all():
            try:
                profile = period.user.userprofile
            except UserProfile.DoesNotExist:
                continue

            # Features from WellnessLog (last 3 days)
            wellness_features = get_recent_wellness_features(period.user, period.start_date, days=3)

            # Period-derived features
            num_symptoms = len([s for s in (period.symptoms or "").split(",") if s.strip()])
            num_medication = len([m for m in (period.medication or "").split(",") if m.strip()])
            current_day = 0
            if period.start_date:
                today = pd.Timestamp.today().date()
                end = period.end_date or period.predicted_end_date or period.start_date
                if period.start_date <= today <= end:
                    current_day = (today - period.start_date).days + 1
            days_to_next = (period.next_period_start_date - (end or pd.Timestamp.today().date())).days if period.next_period_start_date else 0

            rows.append({
                # main
                "user_id": period.user.id,
                "period_id": period.id,
                "gender": profile.sex or "none",
                "cycle_length": period.cycle_length or profile.cycle_length,
                "period_duration": period.period_duration or profile.period_duration,
                "current_day_in_cycle": current_day,
                "num_symptoms": num_symptoms,
                "num_medication": num_medication,
                "days_to_next_period": days_to_next,
                **wellness_features,
                "is_feedback": 0,
                "primary_label": None,
                "secondary_labels": None,
                "response_text": None
            })

        real_data_count = len(rows) - real_data_start
        self.stdout.write(f"   Loaded {real_data_count} real period samples")

        # --- 3. Include AISuggestion feedback data with fresh wellness data ---
        feedback_start = len(rows)
        feedback_suggestions = AISuggestion.objects.filter(feedback=True).select_related('user', 'period')
        for fb in feedback_suggestions:
            # Parse stored features safely
            import json
            try:
                feature_dict = json.loads(fb.features) if fb.features else {}
            except (json.JSONDecodeError, ValueError):
                try:
                    feature_dict = eval(fb.features) if fb.features else {}
                except:
                    feature_dict = {}
            
            # Get fresh wellness data if period is available
            if fb.period and fb.period.start_date:
                wellness_features = get_recent_wellness_features(fb.user, fb.period.start_date, days=3)
            else:
                # Use stored wellness features or defaults
                wellness_features = {
                    "stress_level": feature_dict.get("stress_level", 0),
                    "sleep_hours": feature_dict.get("sleep_hours", 7),
                    "mood_level": feature_dict.get("mood_level", 0),
                    "energy_level": feature_dict.get("energy_level", 5),
                    "pain_level": feature_dict.get("pain_level", 0),
                    "exercise_minutes": feature_dict.get("exercise_minutes", 0),
                    "nutrition_quality": feature_dict.get("nutrition_quality", 3),
                    "caffeine_intake": feature_dict.get("caffeine_intake", 0),
                    "alcohol_intake": feature_dict.get("alcohol_intake", 0),
                    "smoking": feature_dict.get("smoking", 0),
                    "anxiety_level": feature_dict.get("anxiety_level", 0),
                    "focus_level": feature_dict.get("focus_level", 0),
                    "has_wellness_logs": feature_dict.get("has_wellness_logs", 0)
                }
            
            rows.append({
                "user_id": fb.user.id,
                "period_id": fb.period.id if fb.period else None,
                "gender": feature_dict.get("gender", "none"),
                "cycle_length": feature_dict.get("cycle_length", 28),
                "period_duration": feature_dict.get("period_duration", 5),
                "current_day_in_cycle": feature_dict.get("current_day_in_cycle", 0),
                "num_symptoms": feature_dict.get("num_symptoms", 0),
                "num_medication": feature_dict.get("num_medication", 0),
                "days_to_next_period": feature_dict.get("days_to_next_period", 0),
                **wellness_features,
                "is_feedback": 1,
                "primary_label": fb.corrected_label or fb.primary_label,
                "secondary_labels": fb.secondary_labels,
                "response_text": fb.response_text
            })

        feedback_count = len(rows) - feedback_start
        self.stdout.write(f"   Loaded {feedback_count} feedback samples")

        df = pd.DataFrame(rows)
        
        # Log training data statistics
        total_samples = len(df)
        feedback_samples = len(df[df['is_feedback'] == 1])
        wellness_samples = len(df[df['has_wellness_logs'] == 1])
        feedback_with_wellness = len(df[(df['is_feedback'] == 1) & (df['has_wellness_logs'] == 1)])
        synthetic_samples = len(df[df['user_id'].isna()])
        
        self.stdout.write(f"\n📊 Training Data Statistics:")
        self.stdout.write(f"   Total samples: {total_samples}")
        self.stdout.write(f"   Synthetic samples: {synthetic_samples} ({synthetic_samples/total_samples*100:.1f}%)")
        self.stdout.write(f"   Real period samples: {real_data_count} ({real_data_count/total_samples*100:.1f}%)")
        self.stdout.write(f"   Feedback samples: {feedback_samples} ({feedback_samples/total_samples*100:.1f}%)")
        self.stdout.write(f"   Samples with wellness data: {wellness_samples} ({wellness_samples/total_samples*100:.1f}%)")
        self.stdout.write(f"   Feedback + Wellness: {feedback_with_wellness} ({feedback_with_wellness/total_samples*100:.1f}%)")
        self.stdout.write("")
        
        df.fillna({
            "days_to_next_period": 0,
            "stress_level": 0,
            "sleep_hours": 0,
            "current_day_in_cycle": 0,
            "mood_level": 0,
            "energy_level": 5,
            "pain_level": 0,
            "exercise_minutes": 0,
            "nutrition_quality": 3,
            "caffeine_intake": 0,
            "alcohol_intake": 0,
            "smoking": 0,
            "anxiety_level": 0,
            "focus_level": 0
        }, inplace=True)

        # --- 3. Encode gender ---
        df['gender'] = df['gender'].map({'male': 0, 'female': 1, 'none': 2}).fillna(2)

        # --- 4. Multi-hot encode secondary labels ---
        df['secondary_labels'] = df['secondary_labels'].fillna('')
        all_secondary_labels = set()
        for labels in df['secondary_labels']:
            if labels and str(labels) != 'nan':
                all_secondary_labels.update(str(labels).split(';'))
        all_secondary_labels.discard('')
        all_secondary_labels.discard('nan')
        for label in all_secondary_labels:
            df[label] = df['secondary_labels'].apply(lambda x: 1 if label in str(x).split(';') else 0)

        # --- 5. Define features ---
        feature_cols = [
            "gender", "cycle_length", "period_duration", "num_symptoms", 
            "num_medication", "stress_level", "sleep_hours", 
            "days_to_next_period", "current_day_in_cycle",
            "mood_level", "energy_level", "pain_level", "exercise_minutes",
            "nutrition_quality", "caffeine_intake", "alcohol_intake",
            "smoking", "anxiety_level", "focus_level"
        ] + list(all_secondary_labels)

        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0

        X = df[feature_cols]
        y_label = df["primary_label"].fillna("Unknown")

        # --- 6. Build sample weights and split train/test ---
        def compute_weight(row):
            # Higher weight for user feedback; lower for unlabeled/unknown
            base = 3.0 if row.get("is_feedback", 0) == 1 else (0.5 if pd.isna(row.get("primary_label")) or str(row.get("primary_label")).lower() in ["unknown", "none", "nan"] else 1.0)
            
            # Boost for wellness data availability
            wellness_boost = 1.5 if int(row.get("has_wellness_logs", 0)) == 1 else 1.0
            
            # Extra boost for feedback WITH wellness data (most valuable training data)
            if row.get("is_feedback", 0) == 1 and int(row.get("has_wellness_logs", 0)) == 1:
                wellness_boost = 2.0  # Even higher weight for feedback with wellness context
            
            return base * wellness_boost

        sample_weight = df.apply(compute_weight, axis=1).astype(float).values

        # Check if we have enough samples for training
        min_samples = 10
        if len(X) < min_samples:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  Insufficient data: Only {len(X)} samples found (minimum {min_samples} required)."
            ))
            self.stdout.write(self.style.WARNING(
                "Please add more Period data or WellnessLog entries, then try again."
            ))
            return

        # Check if we can do stratified split
        label_counts = y_label.value_counts()
        min_label_count = label_counts.min()
        
        if min_label_count < 2 or len(X) < 10:
            # Too few samples for proper split, use all data for training
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  Small dataset ({len(X)} samples). Using all data for training (no test split)."
            ))
            X_train = X
            y_train_label = y_label
            sw_train = sample_weight
            X_test = X.iloc[:1]  # Use first sample for dummy test
            y_test_label = y_label.iloc[:1]
            sw_test = sample_weight[:1]
            use_test_split = False
        else:
            # Normal train/test split
            X_train, X_test, y_train_label, y_test_label, sw_train, sw_test = train_test_split(
                X, y_label, sample_weight, test_size=0.2, random_state=42, stratify=y_label
            )
            use_test_split = True

        # --- 7. Encode primary_label ---
        # Filter out any None or Unknown labels before training
        valid_mask = y_label.notna() & (y_label != "Unknown") & (y_label != "None") & (y_label != "")
        if not valid_mask.all():
            removed_count = (~valid_mask).sum()
            self.stdout.write(self.style.WARNING(f"⚠️  Removing {removed_count} samples with Unknown/None labels"))
            X = X[valid_mask]
            y_label = y_label[valid_mask]
            sample_weight = sample_weight[valid_mask]
            
            # Re-split if needed
            if use_test_split and len(X) >= 10:
                X_train, X_test, y_train_label, y_test_label, sw_train, sw_test = train_test_split(
                    X, y_label, sample_weight, test_size=0.2, random_state=42, stratify=y_label
                )
            else:
                X_train = X
                y_train_label = y_label
                sw_train = sample_weight
                X_test = X.iloc[:1]
                y_test_label = y_label.iloc[:1]
                sw_test = sample_weight[:1]
                use_test_split = False
        
        le_label = LabelEncoder()
        le_label.fit(y_train_label)
        y_train_label_encoded = le_label.transform(y_train_label)
        y_test_label_encoded = le_label.transform(
            y_test_label.map(lambda x: x if x in le_label.classes_ else y_train_label.iloc[0])
        )

        # --- 8. Train XGB ---
        # Adjust parameters for small datasets
        n_estimators = min(100, max(10, len(X_train) // 2))
        max_depth = min(6, max(2, len(X_train) // 5))
        
        model_label = XGBClassifier(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            learning_rate=0.1,
            eval_metric="mlogloss", 
            random_state=42,
            base_score=0.5  # Explicitly set base_score
        )
        model_label.fit(X_train, y_train_label_encoded, sample_weight=sw_train)
        
        if use_test_split:
            acc_label = accuracy_score(y_test_label_encoded, model_label.predict(X_test), sample_weight=sw_test)
            self.stdout.write(f"📊 primary_label Accuracy: {acc_label:.3f}")
        else:
            acc_label = None  # No accuracy for small datasets without test split
            self.stdout.write(f"📊 Model trained on {len(X_train)} samples (no test split due to small dataset)")

        # --- 9. Generate Transformer responses with caching ---
        cache_file = os.path.join(CACHE_PATH, "response_cache.csv")
        if os.path.exists(cache_file):
            cache_df = pd.read_csv(cache_file)
        else:
            cache_df = pd.DataFrame(columns=["primary_label", "response_text"])

        label_to_response = dict(zip(cache_df.primary_label, cache_df.response_text))

        def get_or_generate_response(row):
            label = row["primary_label"]
            if label in label_to_response:
                return label_to_response[label]
            features_dict = {k: row[k] for k in feature_cols}
            text = generate_health_response(label, features_dict)
            label_to_response[label] = text
            return text

        df["response_text"] = df.apply(get_or_generate_response, axis=1)

        # Save cache
        pd.DataFrame(label_to_response.items(), columns=["primary_label", "response_text"]).to_csv(cache_file, index=False)
        self.stdout.write("✅ Transformer responses generated and cached.")

        # --- 10. Save XGB model ---
        joblib.dump({
            "model": model_label,
            "encoder": le_label,
            "columns": X.columns.tolist(),
            "version": "v4",
            "accuracy": acc_label if acc_label is not None else "N/A (small dataset)",
            "training_samples": len(X_train)
        }, os.path.join(MODEL_PATH, "suggestion_model.pkl"))

        self.stdout.write(self.style.SUCCESS("🎯 Training complete. Models saved successfully!"))
