from rest_framework import serializers
from .models import Period, Ovulation, Partner, WellnessLog
from notifications.models import Notification, NotificationPreference
from django.contrib.auth.models import User


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ['id', 'start_date','predicted_end_date' ,'end_date', 'symptoms', 'medication','cycle_length','period_duration','next_period_start_date']


    def validate_cycle_length(self, value):
        """Ensure cycle length is within a reasonable range."""
        if value < 21 or value > 45:
            raise serializers.ValidationError("Cycle length must be between 21 and 45 days.")
        return value
    

    def validate_period_duration(self, value):
        """Ensure period duration is within a reasonable range."""
        if value < 2 or value > 10:
            raise serializers.ValidationError("Period duration must be between 2 and 10 days.")
        return value
    
    def validate(self, data):
        """Ensure only female users can create period entries."""
        user = self.context['request'].user
        
        try:
            profile = user.userprofile
            user_gender = profile.sex or 'none'
            
            if user_gender != 'female':
                raise serializers.ValidationError(
                    "Period tracking is only available for female users. "
                    "Male users can track their partner's cycle by linking a partner."
                )
        except Exception as e:
            if "Period tracking is only available" in str(e):
                raise
            raise serializers.ValidationError("User profile not found.")
        
        return data
    
    def create(self, validated_data):
        """Associate the period with the authenticated user."""
        user = self.context['request'].user
        validated_data['user'] = user
        return Period.objects.create(**validated_data)
    


class OvulationSerializer(serializers.ModelSerializer):
    ovulation_data = serializers.SerializerMethodField()
    class Meta:
        model = Ovulation
        fields = ['id', 'period', 'ovulation_data']

    def get_ovulation_data(self, obj):
        return obj.predict_ovulation()

class WellnessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellnessLog
        fields = '__all__'
        read_only_fields = ['user']  



# Notification serializers moved to notifications app
# Import them if needed: from notifications.serializers import NotificationSerializer, NotificationPreferenceSerializer
