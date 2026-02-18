from rest_framework.views import APIView
from rest_framework import viewsets ,status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from cycle_tracker.models import WellnessLog
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum, Q, F
from .serializers import DashboardMetricsSerializer, WellnessLogSerializer


class WellnessDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):

        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not  start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()

        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

        logs = WellnessLog.objects.filter(
            user = user,
            date__gte=start_date,
            date__lte=end_date            
        ).order_by('date')

        if not logs.exists():
            return Response({
                'message': 'No wellness data found for the selected period',
                'start_date': start_date,
                'end_date': end_date
            }, status=status.HTTP_200_OK)
        

        averages = logs.aggregate(
                    avg_stress=Avg('stress_level'),
                    avg_sleep=Avg('sleep_hours'),
                    avg_mood=Avg('mood_level'),
                    avg_energy=Avg('energy_level'),
                    avg_pain=Avg('pain_level'),
                    avg_exercise=Avg('exercise_minutes'),
                    avg_nutrition=Avg('nutrition_quality')
                )
        recent_logs = logs.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('date')

        stress_trend = []
        sleep_trend = []
        mood_trend = []


        for log in recent_logs:
            stress_trend.append({
                'date': log.date,
                'value': log.stress_level
            })
            sleep_trend.append({
                'date': log.date,
                'value': log.sleep_hours
            })
            mood_trend.append({
                'date': log.date,
                'value': log.mood_level
            })
        
        # Calculate health indicators
        good_days_count = logs.filter(
            mood_level__gte=7,
            stress_level__lte=3,
            sleep_hours__gte=7
        ).count()
        
        poor_sleep_days = logs.filter(sleep_hours__lt=6).count()
        high_stress_days = logs.filter(stress_level__gte=7).count()
        
        # Get 5 most recent entries for detail view
        recent_entries = logs.order_by('-date')[:5]
        
        # Prepare response data
        dashboard_data = {
            'start_date': start_date,
            'end_date': end_date,
            'avg_stress': round(averages['avg_stress'] or 0, 1),
            'avg_sleep': round(averages['avg_sleep'] or 0, 1),
            'avg_mood': round(averages['avg_mood'] or 0, 1),
            'avg_energy': round(averages['avg_energy'] or 0, 1),
            'avg_pain': round(averages['avg_pain'] or 0, 1),
            'avg_exercise': round(averages['avg_exercise'] or 0, 1),
            'avg_nutrition': round(averages['avg_nutrition'] or 0, 1),
            'stress_trend': stress_trend,
            'sleep_trend': sleep_trend,
            'mood_trend': mood_trend,
            'recent_logs': WellnessLogSerializer(recent_entries, many=True).data,
            'good_days_count': good_days_count,
            'poor_sleep_days': poor_sleep_days,
            'high_stress_days': high_stress_days,
            'total_days_logged': logs.count(),
        }
        
        serializer = DashboardMetricsSerializer(data=dashboard_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)

class WellnessComparisonView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Compare this week vs last week
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        last_week_start = start_of_week - timedelta(days=7)
        last_week_end = end_of_week - timedelta(days=7)
        
        # This week's data
        this_week_logs = WellnessLog.objects.filter(
            user=user,
            date__gte=start_of_week,
            date__lte=end_of_week
        )
        
        # Last week's data
        last_week_logs = WellnessLog.objects.filter(
            user=user,
            date__gte=last_week_start,
            date__lte=last_week_end
        )
        
        # Calculate averages for comparison
        this_week_avg = this_week_logs.aggregate(
            stress=Avg('stress_level'),
            sleep=Avg('sleep_hours'),
            mood=Avg('mood_level'),
            energy=Avg('energy_level')
        )
        
        last_week_avg = last_week_logs.aggregate(
            stress=Avg('stress_level'),
            sleep=Avg('sleep_hours'),
            mood=Avg('mood_level'),
            energy=Avg('energy_level')
        )
        
        return Response({
            'this_week': {
                'period': f'{start_of_week} to {end_of_week}',
                'averages': this_week_avg
            },
            'last_week': {
                'period': f'{last_week_start} to {last_week_end}',
                'averages': last_week_avg
            },
            'comparison': {
                'stress_change': round((this_week_avg['stress'] or 0) - (last_week_avg['stress'] or 0), 1),
                'sleep_change': round((this_week_avg['sleep'] or 0) - (last_week_avg['sleep'] or 0), 1),
                'mood_change': round((this_week_avg['mood'] or 0) - (last_week_avg['mood'] or 0), 1),
                'energy_change': round((this_week_avg['energy'] or 0) - (last_week_avg['energy'] or 0), 1),
            }
        })

class WellnessCorrelationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get last 30 days of data
        start_date = timezone.now().date() - timedelta(days=30)
        logs = WellnessLog.objects.filter(
            user=user,
            date__gte=start_date
        ).order_by('date')
        
        correlations = []
        
        # Simple correlation analysis between different metrics
        metrics_to_analyze = [
            ('sleep_hours', 'energy_level', 'Sleep vs Energy'),
            ('stress_level', 'mood_level', 'Stress vs Mood'),
            ('exercise_minutes', 'stress_level', 'Exercise vs Stress'),
            ('nutrition_quality', 'mood_level', 'Nutrition vs Mood'),
        ]
        
        for metric1, metric2, label in metrics_to_analyze:
            if logs.count() > 1:
                # Calculate correlation coefficient
                values1 = [getattr(log, metric1) for log in logs]
                values2 = [getattr(log, metric2) for log in logs]
                
                # Simple correlation calculation
                if values1 and values2:
                    correlation = self.calculate_correlation(values1, values2)
                    correlations.append({
                        'relationship': label,
                        'correlation': round(correlation, 2),
                        'interpretation': self.interpret_correlation(correlation)
                    })
        
        return Response({
            'correlations': correlations,
            'period': f'Last 30 days ({start_date} to {timezone.now().date()})'
        })
    
    def calculate_correlation(self, x, y):
        """Simple correlation calculation"""
        n = len(x)
        if n <= 1:
            return 0
            
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = (sum((xi - mean_x) ** 2 for xi in x) * sum((yi - mean_y) ** 2 for yi in y)) ** 0.5
        
        if denominator == 0:
            return 0
            
        return numerator / denominator
    
    def interpret_correlation(self, correlation):
        if correlation > 0.7:
            return "Strong positive correlation"
        elif correlation > 0.3:
            return "Moderate positive correlation"
        elif correlation > 0.1:
            return "Weak positive correlation"
        elif correlation < -0.7:
            return "Strong negative correlation"
        elif correlation < -0.3:
            return "Moderate negative correlation"
        elif correlation < -0.1:
            return "Weak negative correlation"
        else:
            return "No significant correlation"

