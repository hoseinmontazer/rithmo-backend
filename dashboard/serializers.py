from rest_framework import serializers
from cycle_tracker.models import WellnessLog
from django.contrib.auth.models import User
from datetime import date, datetime

class WellnessLogSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = WellnessLog
        fields = '__all__'
        read_only_fields = ('user', 'date')
    def get_date(self, obj):
        return obj.date if isinstance(obj.date, date) else obj.date.date()

class DashboardMetricsSerializer(serializers.Serializer):
    # Date range
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    # Aggregated metrics
    avg_stress = serializers.FloatField()
    avg_sleep = serializers.FloatField()
    avg_mood = serializers.FloatField()
    avg_energy = serializers.FloatField()
    avg_pain = serializers.FloatField()
    avg_exercise = serializers.FloatField()
    avg_nutrition = serializers.FloatField()
    
    # Trends
    stress_trend = serializers.ListField(child=serializers.DictField())
    sleep_trend = serializers.ListField(child=serializers.DictField())
    mood_trend = serializers.ListField(child=serializers.DictField())
    
    # Recent entries
    recent_logs = WellnessLogSerializer(many=True)
    
    # Health indicators
    good_days_count = serializers.IntegerField()
    poor_sleep_days = serializers.IntegerField()
    high_stress_days = serializers.IntegerField()