from rest_framework import serializers
from .models import (
    MedicationType, Medication, UserMedication, 
    MedicationLog, MedicationReminder, MedicationInteraction
)


class MedicationTypeSerializer(serializers.ModelSerializer):
    medications_count = serializers.SerializerMethodField()

    class Meta:
        model = MedicationType
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active', 'medications_count']

    def get_medications_count(self, obj):
        return obj.medications.filter(is_active=True).count()


class MedicationSerializer(serializers.ModelSerializer):
    medication_type_name = serializers.CharField(source='medication_type.name', read_only=True)

    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'medication_type', 'medication_type_name',
            'description', 'common_dosages', 'side_effects', 'contraindications',
            'is_prescription', 'is_active'
        ]


class UserMedicationSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(read_only=True)
    medication_details = MedicationSerializer(source='medication', read_only=True)
    logs_count = serializers.SerializerMethodField()
    last_taken = serializers.SerializerMethodField()

    class Meta:
        model = UserMedication
        fields = [
            'id', 'medication', 'custom_name', 'medication_name', 'medication_details',
            'dosage', 'frequency', 'custom_frequency', 'start_date', 'end_date',
            'notes', 'is_active', 'logs_count', 'last_taken', 'created_at'
        ]
        read_only_fields = ['user']
    
    def get_logs_count(self, obj):
        return obj.logs.count()

    def get_last_taken(self, obj):
        last_log = obj.logs.first()
        return last_log.date_taken if last_log else None

    def validate(self, attrs):
            user = self.context['request'].user
            medication = attrs.get('medication',self.instance.medication if self.instance else None)
            qs = UserMedication.objects.filter(user=user, medication=medication)

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise serializers.ValidationError({
                    'medication': 'This medication is already added for the user.'
                })

            return attrs


class MedicationLogSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='user_medication.medication_name', read_only=True)
    user_medication_details = UserMedicationSerializer(source='user_medication', read_only=True)

    class Meta:
        model = MedicationLog
        fields = [
            'id', 'user_medication', 'medication_name', 'user_medication_details',
            'date_taken', 'dosage_taken', 'effectiveness', 'side_effects_experienced',
            'notes', 'created_at'
        ]
        read_only_fields = ['user']

    def validate_effectiveness(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Effectiveness must be between 1 and 5")
        return value


class MedicationReminderSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='user_medication.medication_name', read_only=True)
    user_medication_details = UserMedicationSerializer(source='user_medication', read_only=True)

    class Meta:
        model = MedicationReminder
        fields = [
            'id', 'user_medication', 'medication_name', 'user_medication_details',
            'reminder_time', 'is_active', 'days_of_week', 'created_at'
        ]
        read_only_fields = ['user']

    def validate_days_of_week(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Days of week must be a list")
        
        for day in value:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise serializers.ValidationError("Days must be integers between 0 (Monday) and 6 (Sunday)")
        
        return value


class MedicationInteractionSerializer(serializers.ModelSerializer):
    medication1_name = serializers.CharField(source='medication1.name', read_only=True)
    medication2_name = serializers.CharField(source='medication2.name', read_only=True)

    class Meta:
        model = MedicationInteraction
        fields = [
            'id', 'medication1', 'medication1_name', 'medication2', 'medication2_name',
            'interaction_type', 'description', 'recommendation', 'is_active'
        ]


class UserMedicationSummarySerializer(serializers.Serializer):
    """Summary serializer for user's medication overview"""
    total_medications = serializers.IntegerField()
    active_medications = serializers.IntegerField()
    daily_medications = serializers.IntegerField()
    as_needed_medications = serializers.IntegerField()
    recent_logs_count = serializers.IntegerField()
    medication_types = serializers.ListField()
    upcoming_reminders = serializers.ListField()
    potential_interactions = serializers.ListField()