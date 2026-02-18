#!/usr/bin/env python3
"""
Standalone AI model training script that works with synthetic data only.
This bypasses Django ORM to avoid database connection issues.
"""

import os
import joblib
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml_models")
CACHE_PATH = os.path.join(BASE_DIR, "ml_cache")
os.makedirs(MODEL_PATH, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)

def main():
    print("🚀 Starting standalone AI model training...")
    
    # Load synthetic data
    synthetic_csv = os.path.join(BASE_DIR, "training_dataset.csv")
    if not os.path.exists(synthetic_csv):
        print(f"❌ Training dataset not found at {synthetic_csv}")
        return
    
    print("📂 Loading synthetic training data...")
    df = pd.read_csv(synthetic_csv)
    print(f"   Loaded {len(df)} samples")
    
    # Filter out samples without labels
    labeled_df = df[df['primary_label'].notna() & (df['primary_label'] != '') & (df['primary_label'] != 'Unknown')]
    print(f"   Found {len(labeled_df)} labeled samples")
    
    if len(labeled_df) < 10:
        print("❌ Insufficient labeled data for training")
        return
    
    # Prepare features
    feature_cols = [
        "gender", "cycle_length", "period_duration", "num_symptoms", 
        "num_medication", "stress_level", "sleep_hours", 
        "days_to_next_period", "current_day_in_cycle",
        "mood_level", "energy_level", "pain_level", "exercise_minutes",
        "nutrition_quality", "caffeine_intake", "alcohol_intake",
        "smoking", "anxiety_level", "focus_level"
    ]
    
    # Handle missing columns
    for col in feature_cols:
        if col not in labeled_df.columns:
            labeled_df[col] = 0
    
    # Fill missing values
    labeled_df = labeled_df.fillna({
        "days_to_next_period": 0,
        "stress_level": 0,
        "sleep_hours": 7,
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
    })
    
    # Encode gender
    labeled_df['gender'] = labeled_df['gender'].map({'male': 0, 'female': 1, 'none': 2}).fillna(2)
    
    # Prepare features and labels
    X = labeled_df[feature_cols]
    y = labeled_df['primary_label']
    
    print(f"📊 Training Data Statistics:")
    print(f"   Total labeled samples: {len(X)}")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Unique labels: {y.nunique()}")
    print(f"   Label distribution:")
    for label, count in y.value_counts().head(10).items():
        print(f"     {label}: {count}")
    
    # Check if we can do train/test split
    label_counts = y.value_counts()
    min_label_count = label_counts.min()
    
    if min_label_count < 2 or len(X) < 20:
        print(f"⚠️  Small dataset ({len(X)} samples). Using all data for training.")
        X_train = X
        y_train = y
        X_test = X.iloc[:1]
        y_test = y.iloc[:1]
        use_test_split = False
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        use_test_split = True
    
    # Encode labels
    le_label = LabelEncoder()
    le_label.fit(y_train)
    y_train_encoded = le_label.transform(y_train)
    
    if use_test_split:
        # Handle test labels that might not be in training set
        y_test_mapped = y_test.map(lambda x: x if x in le_label.classes_ else y_train.iloc[0])
        y_test_encoded = le_label.transform(y_test_mapped)
    
    # Train model
    print("🤖 Training XGBoost model...")
    n_estimators = min(100, max(10, len(X_train) // 2))
    max_depth = min(6, max(2, len(X_train) // 5))
    
    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=0.1,
        eval_metric="mlogloss",
        random_state=42,
        base_score=0.5
    )
    
    model.fit(X_train, y_train_encoded)
    
    # Evaluate
    if use_test_split:
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test_encoded, y_pred)
        print(f"📊 Model Accuracy: {accuracy:.3f}")
    else:
        accuracy = "N/A (no test split)"
        print(f"📊 Model trained on {len(X_train)} samples")
    
    # Save model
    model_bundle = {
        "model": model,
        "encoder": le_label,
        "columns": X.columns.tolist(),
        "version": "v4_standalone",
        "accuracy": accuracy,
        "training_samples": len(X_train)
    }
    
    model_file = os.path.join(MODEL_PATH, "suggestion_model.pkl")
    joblib.dump(model_bundle, model_file)
    
    print(f"✅ Model saved to {model_file}")
    print("🎯 Training complete!")
    
    # Test prediction
    print("\n🧪 Testing prediction...")
    sample_features = {
        "gender": 1,  # female
        "cycle_length": 28,
        "period_duration": 5,
        "current_day_in_cycle": 14,  # ovulation
        "num_symptoms": 2,
        "num_medication": 0,
        "days_to_next_period": 14,
        "stress_level": 3,
        "sleep_hours": 7,
        "mood_level": 0,
        "energy_level": 6,
        "pain_level": 1,
        "exercise_minutes": 30,
        "nutrition_quality": 4,
        "caffeine_intake": 1,
        "alcohol_intake": 0,
        "smoking": 0,
        "anxiety_level": 2,
        "focus_level": 3
    }
    
    test_df = pd.DataFrame([sample_features])
    test_df = test_df[feature_cols]  # Ensure column order
    
    pred_idx = model.predict(test_df)[0]
    pred_label = le_label.inverse_transform([pred_idx])[0]
    
    print(f"   Sample prediction: {pred_label}")
    print("   Model is working correctly! ✅")

if __name__ == "__main__":
    main()