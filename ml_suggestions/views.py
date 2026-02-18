# cycle_tracker/views.py
import os
import random
import joblib
import pandas as pd
import logging
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from cycle_tracker.models import Period
from ml_suggestions.models import AISuggestion
# from ml_suggestions.management.commands.response import get_suggestion_explanation
from user_profile.models import UserProfile
from datetime import date
from rest_framework.views import APIView

# Set up logger for this module
logger = logging.getLogger('ml_suggestions')

MODEL_FILE = os.path.join(settings.BASE_DIR, "ml_models", "suggestion_model.pkl")

def load_model():
    """Load the trained model bundle"""
    if os.path.exists(MODEL_FILE):
        try:
            logger.debug(f"Loading model from {MODEL_FILE}")
            model_bundle = joblib.load(MODEL_FILE)
            logger.info(f"Model loaded successfully: version {model_bundle.get('version', 'unknown')}, accuracy {model_bundle.get('accuracy', 'unknown')}")
            return model_bundle
        except Exception as e:
            logger.error(f"Error loading model from {MODEL_FILE}: {e}", exc_info=True)
            return None
    else:
        logger.warning(f"Model file not found: {MODEL_FILE}")
    return None

class  AiSuggetion:


    def get_rule_based_suggestion(self,feature_data):
        """Fallback rule-based suggestions when model is unavailable"""
        gender = feature_data.get('gender', 'none')
        current_day = feature_data.get('current_day_in_cycle', 0)
        num_symptoms = feature_data.get('num_symptoms', 0)
        num_medication = feature_data.get('num_medication', 0)
        stress_level = feature_data.get('stress_level', 0)
        sleep_hours = feature_data.get('sleep_hours', 7)
        cycle_length = feature_data.get('cycle_length', 28)
        
        if gender == "female":
            ov_day = cycle_length // 2
            fertile_start = ov_day - 3
            fertile_end = ov_day + 2
            
            if current_day == 0:
                return "No active period: maintain healthy habits"
            elif current_day == ov_day:
                return "Ovulation day: track symptoms closely"
            elif fertile_start <= current_day <= fertile_end:
                return "Fertile window: track symptoms & take care"
            elif cycle_length < 23:
                return "Unusually short cycle: monitor closely"
            elif cycle_length > 40:
                return "Unusually long cycle: consult if recurring"
            elif num_symptoms >= 4 or stress_level >= 4:
                return "Severe symptoms/stress: rest & consult"
            elif num_symptoms >= 3 and num_medication > 0:
                return "Rest & Take medication"
            elif sleep_hours < 6:
                return "Lack of sleep: prioritize rest"
            elif num_medication > 0:
                return "Take medication"
            else:
                return random.choice([
                    "Balanced nutrition", "Exercise lightly", "Hydrate & Rest", "Mindfulness recommended"
                ])
        else:
            if num_symptoms >= 4 or stress_level >= 4:
                return "Severe stress/symptoms: rest & consult"
            elif num_symptoms >= 2:
                return "Moderate symptoms: monitor & hydrate"
            elif sleep_hours < 6:
                return "Poor sleep: get more rest"
            elif num_medication > 0:
                return "Take medication"
            elif stress_level >= 3:
                return "High stress: relax & hydrate"
            else:
                return random.choice([
                    "Stay active", "Balanced nutrition", "Exercise lightly", 
                    "Get enough sleep", "Hydrate & Relax"
                ])



    def get_secondary_labels(self,feature_data):
        """Generate secondary labels for the suggestion"""
        labels = []
        
        gender = feature_data.get('gender', 'none')
        current_day = feature_data.get('current_day_in_cycle', 0)
        cycle_length = feature_data.get('cycle_length', 28)
        num_symptoms = feature_data.get('num_symptoms', 0)
        num_medication = feature_data.get('num_medication', 0)
        stress_level = feature_data.get('stress_level', 0)
        sleep_hours = feature_data.get('sleep_hours', 7)
        
        # Fertility-related labels for females
        if gender == "female":
            ov_day = cycle_length // 2
            fertile_start = ov_day - 3
            fertile_end = ov_day + 2
            
            if fertile_start <= current_day <= fertile_end:
                labels.append("fertile_window")
            if current_day == ov_day:
                labels.append("ovulation_day")
            if current_day == 1:
                labels.append("period_start")
        
        # General health labels
        if num_medication > 0:
            labels.append("medication_taken")
        if num_symptoms > 0:
            labels.append("symptoms_present")
        if stress_level >= 3:
            labels.append("high_stress")
        if sleep_hours < 6:
            labels.append("sleep_deprivation")
        if feature_data.get('days_to_next_period', 0) <= 2:
            labels.append("period_approaching")
        
        return ";".join(labels)


    def prepare_features(self, user, profile, period):
        """Prepare features exactly as training data format with wellness logs"""
        from cycle_tracker.models import WellnessLog
        import numpy as np
        
        # Calculate current day in cycle
        current_day = 0
        if period and period.start_date:
            today = date.today()
            end_date = period.end_date or period.predicted_end_date
            if period.start_date <= today <= (end_date or today):
                current_day = (today - period.start_date).days + 1

        # Calculate days to next period
        days_to_next = 0
        if period and period.next_period_start_date:
            today = date.today()
            days_to_next = max(0, (period.next_period_start_date - today).days)

        # Get symptoms and medication counts
        num_symptoms = 0
        num_medication = 0
        
        if period:
            if period.symptoms:
                num_symptoms = len([s for s in period.symptoms.split(',') if s.strip()])
            if period.medication:
                num_medication = len([m for m in period.medication.split(',') if m.strip()])

        # Get recent wellness logs (last 3 days)
        wellness_logs = WellnessLog.objects.filter(user=user).order_by('-date')[:3]
        
        if wellness_logs:
            # Calculate averages from recent wellness logs
            wellness_features = {
                "stress_level": round(np.mean([log.stress_level for log in wellness_logs]), 2),
                "sleep_hours": round(np.mean([log.sleep_hours for log in wellness_logs]), 2),
                "mood_level": round(np.mean([log.mood_level for log in wellness_logs]), 2),
                "energy_level": round(np.mean([log.energy_level for log in wellness_logs]), 2),
                "pain_level": round(np.mean([log.pain_level for log in wellness_logs]), 2),
                "exercise_minutes": round(np.mean([log.exercise_minutes for log in wellness_logs]), 2),
                "nutrition_quality": round(np.mean([log.nutrition_quality for log in wellness_logs]), 2),
                "caffeine_intake": round(np.mean([log.caffeine_intake for log in wellness_logs]), 2),
                "alcohol_intake": round(np.mean([log.alcohol_intake for log in wellness_logs]), 2),
                "smoking": round(np.mean([log.smoking for log in wellness_logs]), 2),
                "anxiety_level": round(np.mean([log.anxiety_level for log in wellness_logs]), 2),
                "focus_level": round(np.mean([log.focus_level for log in wellness_logs]), 2),
                "has_wellness_logs": 1
            }
        else:
            # Default values if no wellness logs
            wellness_features = {
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

        return {
            "gender": profile.sex if profile and profile.sex else "none",
            "cycle_length": period.cycle_length if period and period.cycle_length else (
                profile.cycle_length if profile and profile.cycle_length else 28
            ),
            "period_duration": period.period_duration if period and period.period_duration else (
                profile.period_duration if profile and profile.period_duration else 5
            ),
            "current_day_in_cycle": current_day,
            "num_symptoms": num_symptoms,
            "num_medication": num_medication,
            "days_to_next_period": days_to_next,
            **wellness_features
        }



    def _generate_dynamic_response(self, label, feature_data):
        """Generate dynamic, personalized response based on user's current wellness data"""
        
        # Extract wellness metrics
        stress = feature_data.get('stress_level', 0)
        sleep = feature_data.get('sleep_hours', 7)
        mood = feature_data.get('mood_level', 0)
        energy = feature_data.get('energy_level', 5)
        pain = feature_data.get('pain_level', 0)
        exercise = feature_data.get('exercise_minutes', 0)
        gender = feature_data.get('gender', 'none')
        current_day = feature_data.get('current_day_in_cycle', 0)
        
        # Determine if user is female
        is_female = gender in ['female', 1]
        is_male = gender in ['male', 0]
        
        # Build personalized response parts
        response_parts = []
        
        # Main recommendation based on label
        if "sleep" in label.lower():
            if sleep < 5:
                response_parts.append(f"You're only getting {sleep} hours of sleep, which is significantly below the recommended amount.")
                response_parts.append("Prioritize getting to bed earlier tonight. Aim for 7-8 hours of quality rest.")
            elif sleep < 6:
                response_parts.append(f"With {sleep} hours of sleep, you're running on less rest than ideal.")
                response_parts.append("Try to add an extra hour tonight and establish a calming bedtime routine.")
            else:
                response_parts.append(f"Your sleep of {sleep} hours is good, but there's room for improvement.")
                response_parts.append("Maintain consistent sleep times and create a relaxing evening environment.")
        
        elif "stress" in label.lower():
            response_parts.append(f"Your stress level is at {stress}/5, which needs attention.")
            if exercise < 20:
                response_parts.append("Consider light exercise like a 15-minute walk to help reduce stress.")
            response_parts.append("Practice deep breathing exercises and take short breaks throughout your day.")
            if sleep < 7:
                response_parts.append("Better sleep will also help manage your stress levels.")
        
        elif "energy" in label.lower():
            if energy <= 2:
                response_parts.append(f"Your energy is very low (level {energy}/10).")
                response_parts.append("Take it easy today. Focus on rest, hydration, and nutritious meals.")
                if sleep < 7:
                    response_parts.append(f"Your {sleep} hours of sleep may be contributing to low energy.")
            elif energy <= 4:
                response_parts.append(f"Your energy is below average (level {energy}/10).")
                response_parts.append("Pace yourself with lighter activities and ensure you're eating balanced meals.")
            else:
                response_parts.append(f"Your energy level is good at {energy}/10.")
                response_parts.append("This is a great time for productive activities or exercise.")
        
        elif is_female and ("fertile" in label.lower() or "ovulation" in label.lower()):
            response_parts.append("You're in your fertile window.")
            response_parts.append("Stay hydrated, track any symptoms, and maintain balanced nutrition.")
            if stress >= 3:
                response_parts.append("Try to manage stress levels as they can affect your cycle.")
        
        elif is_female and ("period" in label.lower() or "pms" in label.lower()):
            response_parts.append("During this phase of your cycle, self-care is especially important.")
            if pain >= 3:
                response_parts.append(f"With pain at level {pain}, consider heat therapy and gentle stretching.")
            response_parts.append("Stay hydrated, eat iron-rich foods, and rest when needed.")
            if stress >= 3:
                response_parts.append("Stress management is particularly important during this time.")
        
        elif is_male and ("period" in label.lower() or "fertile" in label.lower() or "ovulation" in label.lower() or "pms" in label.lower()):
            # Male got a female-specific label - provide general wellness advice instead
            response_parts.append("Focus on maintaining your overall health and wellness.")
            if stress >= 3:
                response_parts.append(f"Your stress level is at {stress}/5. Consider stress management techniques.")
            if sleep < 7:
                response_parts.append(f"Improving your sleep from {sleep} hours would benefit your health.")
            if exercise < 30:
                response_parts.append("Regular physical activity can improve your overall wellbeing.")
            if not response_parts or len(response_parts) == 1:
                response_parts.append("Stay hydrated, eat balanced meals, and maintain regular exercise.")
        
        elif "pain" in label.lower():
            response_parts.append(f"You're experiencing pain at level {pain}/10.")
            if pain >= 7:
                response_parts.append("This level of pain warrants medical attention. Please consult a healthcare provider.")
            else:
                response_parts.append("Try rest, heat therapy, and over-the-counter pain relief if appropriate.")
        
        elif "mood" in label.lower() or "anxiety" in label.lower():
            response_parts.append("Your emotional wellness needs attention right now.")
            response_parts.append("Practice mindfulness, connect with supportive people, and engage in activities you enjoy.")
            if exercise < 20:
                response_parts.append("Light physical activity can significantly improve mood.")
        
        else:
            # Generic but personalized response
            response_parts.append(label + ".")
            
            # Gender-specific wellness advice
            if is_male:
                # Male-specific health tips
                if stress >= 4:
                    response_parts.append(f"Your stress level is high ({stress}/5). Consider physical activity or meditation to manage stress.")
                elif stress >= 3:
                    response_parts.append(f"With stress at {stress}/5, take time for activities that help you unwind.")
                
                if exercise == 0:
                    response_parts.append("Regular exercise is crucial for men's health. Start with 20-30 minutes of activity daily.")
                elif exercise > 60:
                    response_parts.append("Great job staying active! Ensure you're balancing exercise with adequate recovery.")
                
                if sleep < 7:
                    response_parts.append(f"Your {sleep} hours of sleep is below optimal. Aim for 7-9 hours for better recovery and energy.")
                
                if energy <= 3 and exercise < 20:
                    response_parts.append("Low energy can be improved with regular physical activity and proper nutrition.")
                
            elif is_female:
                # Female-specific health tips (non-cycle related)
                if stress >= 4:
                    response_parts.append(f"Your stress level is high ({stress}/5). Stress can affect your overall health and cycle regularity.")
                elif stress >= 3:
                    response_parts.append(f"With stress at {stress}/5, prioritize self-care and relaxation techniques.")
                
                if exercise == 0:
                    response_parts.append("Regular movement supports hormonal balance and overall wellness. Try 20-30 minutes of activity daily.")
                elif exercise > 60:
                    response_parts.append("Excellent activity level! Remember to listen to your body and rest when needed.")
                
                if sleep < 7:
                    response_parts.append(f"Your {sleep} hours of sleep may affect your energy and wellness. Aim for 7-9 hours.")
                
                if energy <= 3:
                    response_parts.append("Low energy can be improved with balanced nutrition, adequate rest, and gentle exercise.")
            
            else:
                # Gender-neutral advice
                if stress >= 3:
                    response_parts.append(f"Your stress level ({stress}/5) suggests you need relaxation time.")
                if sleep < 7:
                    response_parts.append(f"Improving your sleep from {sleep} hours would benefit your overall health.")
                if energy <= 3:
                    response_parts.append("Focus on rest and nutrition to boost your energy.")
                elif energy >= 7:
                    response_parts.append("Your good energy levels are perfect for staying active.")
            
            # General wellness tip if not enough specific advice
            if len(response_parts) < 2:
                if is_male:
                    response_parts.append("Maintain a balanced diet, stay hydrated, and prioritize consistent sleep schedules.")
                elif is_female:
                    response_parts.append("Keep up healthy habits with balanced nutrition, hydration, and regular self-care.")
                else:
                    response_parts.append("Keep up your healthy habits with balanced nutrition, regular activity, and adequate rest.")
        
        # Add general wellness tip based on metrics
        if len(response_parts) < 3:
            if exercise == 0:
                response_parts.append("Even 10-15 minutes of movement can make a difference.")
            elif exercise > 60:
                response_parts.append("Great job staying active! Remember to balance activity with rest.")
        
        return " ".join(response_parts)

    def predict_with_model(self, feature_data, model_bundle):
        """Make prediction using the trained model"""
        logger.debug(f"Starting AI prediction with {len(feature_data)} features")

        try:
            X = pd.DataFrame([feature_data])
            logger.debug(f"Created DataFrame with shape {X.shape}")
            
            # Encode gender
            X['gender'] = X['gender'].map({'male':0,'female':1,'none':2}).fillna(2)
            X = X.fillna(0)
            logger.debug(f"Gender encoded and missing values filled")

            # Ensure all training columns exist
            missing_cols = []
            for col in model_bundle["columns"]:
                if col not in X.columns:
                    X[col] = 0
                    missing_cols.append(col)
            
            if missing_cols:
                logger.debug(f"Added missing columns: {missing_cols}")
            
            X = X[model_bundle["columns"]]
            logger.debug(f"Final feature matrix shape: {X.shape}")

            # Predict primary_label
            pred_label_idx = model_bundle["model"].predict(X)[0]
            primary_label = model_bundle["encoder"].inverse_transform([pred_label_idx])[0]
            logger.debug(f"Raw prediction: {primary_label}")
            
            # Fallback if prediction is Unknown or None
            if not primary_label or str(primary_label).lower() in ['unknown', 'none', 'nan']:
                logger.warning(f"Invalid prediction '{primary_label}', using rule-based fallback")
                # Use rule-based as fallback
                from ml_suggestions.views import AiSuggetion
                primary_label = AiSuggetion().get_rule_based_suggestion(feature_data)
                logger.info(f"Rule-based fallback result: {primary_label}")

            # Generate dynamic, personalized response based on current wellness data
            response_text = self._generate_dynamic_response(primary_label, feature_data)
            logger.debug(f"Generated response text: {response_text[:100]}...")

            logger.info(f"AI prediction successful: {primary_label}")
            return {"primary_label": primary_label, "response_text": response_text}

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            raise e


class GetSuggetion(APIView):

    @api_view(["GET"])
    def get_ai_suggestion(request):
        """Get AI-powered suggestion for user"""
        user = request.user
        logger.info(f"AI suggestion requested for user {user.id} ({user.username})")
        
        # Check if user has profile
        try:
            profile = user.userprofile
            logger.debug(f"User profile found for user {user.id}")
        except UserProfile.DoesNotExist:
            logger.warning(f"User profile not found for user {user.id}")
            return Response(
                {"error": "User profile not found. Please complete your profile."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get latest period
        period = Period.objects.filter(user=user).order_by("-start_date").first()
        if period:
            logger.debug(f"Latest period found for user {user.id}: period {period.id}")
        else:
            logger.debug(f"No periods found for user {user.id}")
        
        # Prepare feature data
        feature_data = AiSuggetion().prepare_features(user, profile, period)
        logger.debug(f"Feature data prepared for user {user.id}: {len(feature_data)} features")
        
        # Try to load model
        model_bundle = load_model()
        
        if not model_bundle:
            logger.warning("AI model not available, falling back to rule-based suggestions")
            # Fallback to rule-based suggestions
            suggestion = AiSuggetion().get_rule_based_suggestion(feature_data)
            secondary_labels = AiSuggetion().get_secondary_labels(feature_data)
            logger.info(f"Rule-based suggestion generated for user {user.id}: {suggestion}")
            
            # Save the suggestion
            import json
            ai_suggestion = AISuggestion.objects.create(
                user=user,
                period=period,
                primary_label=suggestion,
                secondary_labels=secondary_labels,
                model_version="rule_based",
                features=json.dumps(feature_data)
            )
            logger.info(f"Rule-based suggestion saved with ID {ai_suggestion.id}")
            
            return Response({
                "label": suggestion,
                "suggestion": "test",
                "id": ai_suggestion.id,
                "model_version": "rule_based",
                "fallback": True,
                "message": "Using rule-based suggestions (AI model not available)"
            })
        
        try:
            logger.info(f"Using AI model for prediction (user {user.id})")
            # Use AI model for prediction
            suggestion = AiSuggetion().predict_with_model(feature_data, model_bundle)
            secondary_labels = AiSuggetion().get_secondary_labels(feature_data)
            logger.info(f"AI prediction successful for user {user.id}: {suggestion['primary_label']}")
            
            # Save the suggestion for feedback tracking
            import json
            ai_suggestion = AISuggestion.objects.create(
                user=user,
                period=period,
                primary_label=suggestion['primary_label'],
                secondary_labels=secondary_labels,
                response_text=suggestion['response_text'],
                model_version=model_bundle.get("version", "v1"),
                features=json.dumps(feature_data)
            )
            logger.info(f"AI suggestion saved with ID {ai_suggestion.id}")

            return Response({
                "suggestion_lable": suggestion['primary_label'],
                "suggestion": suggestion['response_text'],
                "id": ai_suggestion.id,
                "model_version": model_bundle.get("version", "v1"),
                "fallback": False
            })
            
        except Exception as e:
            logger.error(f"AI prediction failed for user {user.id}: {str(e)}", exc_info=True)
            # Fallback if prediction fails
            suggestion = AiSuggetion().get_rule_based_suggestion(feature_data)
            secondary_labels = AiSuggetion().get_secondary_labels(feature_data)
            logger.info(f"Error fallback suggestion for user {user.id}: {suggestion}")
            
            import json
            ai_suggestion = AISuggestion.objects.create(
                user=user,
                period=period,
                primary_label=suggestion,
                secondary_labels=secondary_labels,
                model_version="error_fallback",
                features=json.dumps(feature_data)
            )
            logger.info(f"Error fallback suggestion saved with ID {ai_suggestion.id}")
            
            return Response({
                "suggestion": suggestion,
                "id": ai_suggestion.id,
                "model_version": "error_fallback",
                "fallback": True,
                "error": str(e),
                "message": "Using fallback suggestions due to prediction error"
            })

    @api_view(["POST"])
    def give_feedback(request, suggestion_id):
        """Save user feedback for AI suggestions"""
        user = request.user
        logger.info(f"Feedback request for suggestion {suggestion_id} from user {user.id} ({user.username})")
        
        try:
            feedback = request.data.get("feedback")
            corrected_label = request.data.get("corrected_label", "").strip() if request.data.get("corrected_label") else ""
            response_text = request.data.get("response_text", "").strip() if request.data.get("response_text") else ""
            
            logger.debug(f"Feedback data - feedback: {feedback}, corrected_label: {corrected_label}, response_text: {response_text[:50] if response_text else 'None'}...")
            
            if feedback is None and not corrected_label:
                logger.warning(f"Invalid feedback request from user {user.id}: no feedback or corrected_label provided")
                return Response(
                    {"error": "Either feedback or corrected_label is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the AI suggestion
            try:
                ai_suggestion = AISuggestion.objects.get(id=suggestion_id, user=request.user)
                logger.debug(f"Found suggestion {suggestion_id} for user {user.id}")
            except AISuggestion.DoesNotExist:
                logger.warning(f"Suggestion {suggestion_id} not found for user {user.id}")
                # Log available suggestions for debugging
                user_suggestions = AISuggestion.objects.filter(user=user).values_list('id', flat=True)
                logger.debug(f"Available suggestions for user {user.id}: {list(user_suggestions)}")
                return Response(
                    {"error": "Suggestion not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update fields
            old_feedback = ai_suggestion.feedback
            old_corrected_label = ai_suggestion.corrected_label
            
            if feedback is not None:
                ai_suggestion.feedback = bool(feedback)
            if corrected_label:
                ai_suggestion.corrected_label = corrected_label
            if response_text:
                ai_suggestion.response_text = response_text

            ai_suggestion.save()
            
            logger.info(f"Feedback saved for suggestion {suggestion_id}: feedback {old_feedback} -> {ai_suggestion.feedback}, corrected_label '{old_corrected_label}' -> '{ai_suggestion.corrected_label}'")
            
            return Response({
                "status": "success",
                "message": "Feedback saved successfully",
                "suggestion_id": ai_suggestion.id,
                "feedback": ai_suggestion.feedback,
                "corrected_label": ai_suggestion.corrected_label
            })
            
        except Exception as e:
            logger.error(f"Failed to save feedback for suggestion {suggestion_id}, user {user.id}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to save feedback: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @api_view(["GET"])
    def get_suggestion_history(request):
        """Get user's AI suggestion history"""
        try:
            suggestions = AISuggestion.objects.filter(user=request.user).order_by("-created_at")[:50]
            
            history = []
            for suggestion in suggestions:
                history.append({
                    "id": suggestion.id,
                    "suggestion": suggestion.primary_label,
                    "secondary_labels": suggestion.secondary_labels.split(';') if suggestion.secondary_labels else [],
                    "model_version": suggestion.model_version,
                    "created_at": suggestion.created_at,
                    "feedback": suggestion.feedback,
                    "corrected_label": suggestion.corrected_label,
                    "period_id": suggestion.period.id if suggestion.period else None
                })
            
            return Response({
                "count": len(history),
                "history": history
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @api_view(["GET"])
    def get_model_status(request):
        """Check AI model status and information"""
        model_bundle = load_model()
        
        status_info = {
            "model_available": model_bundle is not None,
            "model_file_exists": os.path.exists(MODEL_FILE),
        }
        
        if model_bundle:
            status_info.update({
                "model_version": model_bundle.get("version", "unknown"),
                "accuracy": model_bundle.get("accuracy", "unknown"),
                "training_samples": model_bundle.get("training_samples", "unknown"),
                "feature_columns": len(model_bundle.get("columns", [])),
            })
        
        return Response(status_info)

    @api_view(["GET"])
    def debug_suggestions(request):
        """Debug endpoint to check user's suggestions"""
        user = request.user
        logger.info(f"Debug suggestions requested for user {user.id} ({user.username})")
        
        try:
            user_suggestions = AISuggestion.objects.filter(user=request.user).values(
                'id', 'primary_label', 'feedback', 'corrected_label', 'created_at', 'model_version'
            )
            
            logger.debug(f"Found {len(user_suggestions)} suggestions for user {user.id}")
            
            return Response({
                "user_id": request.user.id,
                "username": request.user.username,
                "total_suggestions": len(user_suggestions),
                "suggestions": list(user_suggestions)
            })
        except Exception as e:
            logger.error(f"Debug suggestions failed for user {user.id}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=500)

