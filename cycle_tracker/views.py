from rest_framework import viewsets ,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Ovulation, Period, WellnessLog
from notifications.models import Notification, NotificationPreference
from .serializers import OvulationSerializer, PeriodSerializer, WellnessLogSerializer
from notifications.serializers import NotificationSerializer, NotificationPreferenceSerializer



class PeriodViewSet(viewsets.ModelViewSet):
    """Viewset for managing Period tracking."""
    serializer_class = PeriodSerializer
    permission_classes= [IsAuthenticated]


    @action(detail=False, methods=['PATCH'] , url_path='update')
    def update_latest_period(self, request):
        """
        Updates the end_date, symptoms, or medication for the latest period entry of the authenticated user.
        """
        user = request.user
        get_user_period_id = request.data.get('period_id')
        print("---->",get_user_period_id)

        if get_user_period_id is  None:
            return Response({"error": "period_id not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            get_user_period_id = int(get_user_period_id)
        except ValueError:
            return Response({"error": "period_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            latest_period = Period.objects.get(id=get_user_period_id,user=user)
            print(latest_period)
            print("--->",latest_period.symptoms)
            if not latest_period:
                return Response({"error": "No period entry found."}, status=status.HTTP_404_NOT_FOUND)

            # Get the provided data
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            symptoms = request.data.get('symptoms')
            medication = request.data.get('medication')


            # Update `start_date` if provided
            if start_date:
                try:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

                if latest_period.end_date and start_date >= latest_period.end_date:
                    return Response({"error": "start_date must be after end_date."}, status=status.HTTP_400_BAD_REQUEST)

                latest_period.start_date = start_date

            # Update `end_date` if provided
            if end_date:
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

                if end_date <= latest_period.start_date:
                    return Response({"error": "end_date must be after start_date."}, status=status.HTTP_400_BAD_REQUEST)

                latest_period.end_date = end_date

            # Update symptoms & medication if provided
            if symptoms is not None:
                latest_period.symptoms = symptoms
            if medication is not None:
                latest_period.medication = medication

            print("----->",latest_period.symptoms,latest_period.medication,latest_period.start_date,latest_period.end_date)
            latest_period.save()
            return Response({**PeriodSerializer(latest_period).data, "success": True}, status=status.HTTP_200_OK)
        except Period.DoesNotExist:
            return Response({"error": "Period not found for this user"}, status=404)

        # return Response({"message": "Period updated successfully"})



    def get_queryset(self):
        """
        Return queryset based on request role.
        If role is 'partner', return partner's periods if authorized.
        Otherwise return user's own periods.
        """
        user = self.request.user
        # Check both query params and headers for role
        role = self.request.query_params.get('role') or self.request.headers.get('role', 'self')

        if role == 'partner':
            print('partner')
            # Get the user's profile and check if they have any partners
            user_profile = user.userprofile
            partners = user_profile.partners.all()
            print(f"partners: {partners}")
            if not partners.exists():
                return Period.objects.none()
                
            # Get the first partner and their periods
            partner = partners.first()
            partner_user = partner.user
            print(f"partner_user: {partner_user}")
            
            # Add partner info to the request object for use in serializer
            partner_name = f"{partner_user.first_name} {partner_user.last_name}".strip()
            if not partner_name:  # If both first_name and last_name are empty
                partner_name = partner_user.username  # Fall back to username
                
            self.request.partner_info = {
                'partner_name': partner_name,
                'partner_id': partner.id  # Using UserProfile ID instead of User ID
            }
            
            return Period.objects.filter(user=partner_user)
            
        return Period.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Assign the logged-in user as the owner of the period entry."""
        serializer.save(user=self.request.user)




    @action(detail=False, methods=['get'])
    def wellness_correlation(self, request):
        """Analyze correlation between wellness metrics and cycle phases."""
        from datetime import date
        from django.db.models import Avg
        
        try:
            profile = request.user.userprofile
            gender = profile.sex or 'none'
        except:
            gender = 'none'
        
        if gender != 'female':
            return Response({
                'error': 'Wellness correlation is only available for female users'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get periods and wellness logs
        periods = Period.objects.filter(user=request.user).order_by('-start_date')[:6]
        wellness_logs = WellnessLog.objects.filter(user=request.user).order_by('-date')[:90]
        
        if not periods.exists() or not wellness_logs.exists():
            return Response({
                'error': 'Insufficient data for correlation analysis'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Categorize wellness logs by cycle phase
        phase_data = {
            'Menstrual': [],
            'Follicular': [],
            'Ovulation': [],
            'Luteal': [],
            'PMS': []
        }
        
        for log in wellness_logs:
            # Find which period this log belongs to
            phase = self._determine_wellness_phase(log.date, periods)
            if phase and phase in phase_data:
                phase_data[phase].append({
                    'mood': log.mood_level,
                    'energy': log.energy_level,
                    'stress': log.stress_level,
                    'pain': log.pain_level,
                    'sleep': log.sleep_hours,
                    'anxiety': log.anxiety_level
                })
        
        # Calculate averages per phase
        correlations = {}
        for phase, logs in phase_data.items():
            if logs:
                correlations[phase] = {
                    'avg_mood': round(sum(l['mood'] for l in logs) / len(logs), 1),
                    'avg_energy': round(sum(l['energy'] for l in logs) / len(logs), 1),
                    'avg_stress': round(sum(l['stress'] for l in logs) / len(logs), 1),
                    'avg_pain': round(sum(l['pain'] for l in logs) / len(logs), 1),
                    'avg_sleep': round(sum(l['sleep'] for l in logs) / len(logs), 1),
                    'avg_anxiety': round(sum(l['anxiety'] for l in logs) / len(logs), 1),
                    'sample_count': len(logs)
                }
        
        # Generate insights
        insights = self._generate_wellness_insights(correlations)
        
        return Response({
            'status': 'success',
            'data': {
                'phase_correlations': correlations,
                'insights': insights,
                'data_range_days': (wellness_logs.first().date - wellness_logs.last().date).days if wellness_logs.count() > 1 else 0
            }
        })
    
    def _determine_wellness_phase(self, log_date, periods):
        """Determine which cycle phase a wellness log belongs to."""
        for period in periods:
            if period.start_date <= log_date:
                days_since_period = (log_date - period.start_date).days
                cycle_length = period.cycle_length or 28
                
                # Determine phase based on days since period start
                if days_since_period <= 5:
                    return 'Menstrual'
                elif days_since_period <= 13:
                    return 'Follicular'
                elif days_since_period <= 16:
                    return 'Ovulation'
                elif days_since_period <= cycle_length - 4:
                    return 'Luteal'
                elif days_since_period <= cycle_length:
                    return 'PMS'
                
                # Check if it's before next period
                if period.next_period_start_date and log_date < period.next_period_start_date:
                    days_until_next = (period.next_period_start_date - log_date).days
                    if days_until_next <= 3:
                        return 'PMS'
        
        return None
    
    # def _generate_wellness_insights(self, correlations):
    #     """Generate insights from wellness correlations."""
    #     insights = []
        
    #     if not correlations:
    #         return insights
        
    #     # Find phase with lowest energy
    #     energy_by_phase = {phase: data['avg_energy'] for phase, data in correlations.items() if 'avg_energy' in data}
    #     if energy_by_phase:
    #         lowest_energy_phase = min(energy_by_phase, key=energy_by_phase.get)
    #         insights.append(f"Your energy is typically lowest during {lowest_energy_phase} phase ({energy_by_phase[lowest_energy_phase]}/10)")
        
    #     # Find phase with highest stress
    #     stress_by_phase = {phase: data['avg_stress'] for phase, data in correlations.items() if 'avg_stress' in data}
    #     if stress_by_phase:
    #         highest_stress_phase = max(stress_by_phase, key=stress_by_phase.get)
    #         if stress_by_phase[highest_stress_phase] >= 3:
    #             insights.append(f"Stress levels peak during {highest_stress_phase} phase ({stress_by_phase[highest_stress_phase]}/5)")
        
    #     # Find phase with best mood
    #     mood_by_phase = {phase: data['avg_mood'] for phase, data in correlations.items() if 'avg_mood' in data}
    #     if mood_by_phase:
    #         best_mood_phase = max(mood_by_phase, key=mood_by_phase.get)
    #         insights.append(f"Your mood is typically best during {best_mood_phase} phase ({mood_by_phase[best_mood_phase]}/2)")
        
    #     # Pain patterns
    #     pain_by_phase = {phase: data['avg_pain'] for phase, data in correlations.items() if 'avg_pain' in data}
    #     if pain_by_phase:
    #         highest_pain_phase = max(pain_by_phase, key=pain_by_phase.get)
    #         if pain_by_phase[highest_pain_phase] >= 4:
    #             insights.append(f"Pain levels are highest during {highest_pain_phase} phase ({pain_by_phase[highest_pain_phase]}/10)")
        
    #     # Sleep patterns
    #     sleep_by_phase = {phase: data['avg_sleep'] for phase, data in correlations.items() if 'avg_sleep' in data}
    #     if sleep_by_phase:
    #         best_sleep_phase = max(sleep_by_phase, key=sleep_by_phase.get)
    #         worst_sleep_phase = min(sleep_by_phase, key=sleep_by_phase.get)
    #         if sleep_by_phase[best_sleep_phase] - sleep_by_phase[worst_sleep_phase] >= 1:
    #             insights.append(f"You sleep {sleep_by_phase[best_sleep_phase] - sleep_by_phase[worst_sleep_phase]:.1f} hours more during {best_sleep_phase} than {worst_sleep_phase}")
        
    #     return insights

    @action(detail=False, methods=['get'])
    def cycle_insights(self, request):
        """Get personalized cycle insights and predictions."""
        from datetime import date
        
        try:
            profile = request.user.userprofile
            gender = profile.sex or 'none'
        except:
            gender = 'none'
        
        if gender != 'female':
            return Response({
                'error': 'Cycle insights are only available for female users'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        periods = Period.objects.filter(user=request.user).order_by('-start_date')[:12]
        
        if periods.count() < 2:
            return Response({
                'error': 'Need at least 2 periods for insights'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_period = periods.first()
        insights = []
        warnings = []
        
        # Analyze cycle regularity trend
        if periods.count() >= 6:
            recent_cycles = [
                (periods[i].start_date - periods[i+1].start_date).days
                for i in range(min(3, periods.count()-1))
            ]
            older_cycles = [
                (periods[i].start_date - periods[i+1].start_date).days
                for i in range(3, min(6, periods.count()-1))
            ]
            
            if recent_cycles and older_cycles:
                from statistics import stdev
                recent_std = stdev(recent_cycles) if len(set(recent_cycles)) > 1 else 0
                older_std = stdev(older_cycles) if len(set(older_cycles)) > 1 else 0
                
                if recent_std < older_std - 1:
                    insights.append("Your cycles are becoming more regular")
                elif recent_std > older_std + 1:
                    warnings.append("Your cycles are becoming less regular - consider tracking more factors")
        
        # Check for unusual cycle length
        if periods.count() >= 3:
            cycle_lengths = [
                (periods[i].start_date - periods[i+1].start_date).days
                for i in range(periods.count()-1)
            ]
            avg_cycle = sum(cycle_lengths) / len(cycle_lengths)
            current_cycle = cycle_lengths[0] if cycle_lengths else None
            
            if current_cycle and abs(current_cycle - avg_cycle) > 5:
                warnings.append(f"Last cycle was {abs(current_cycle - avg_cycle):.0f} days {'longer' if current_cycle > avg_cycle else 'shorter'} than your average")
        
        # Symptom patterns
        recent_periods_with_symptoms = periods.filter(symptoms__isnull=False).exclude(symptoms='')[:3]
        if recent_periods_with_symptoms.count() >= 2:
            insights.append(f"You've tracked symptoms for {recent_periods_with_symptoms.count()} recent periods - great job!")
        
        # Period duration analysis
        periods_with_duration = [p for p in periods if p.end_date]
        if len(periods_with_duration) >= 3:
            durations = [(p.end_date - p.start_date).days for p in periods_with_duration[:3]]
            avg_duration = sum(durations) / len(durations)
            
            if avg_duration < 3:
                warnings.append("Your periods are shorter than average - consider discussing with a healthcare provider")
            elif avg_duration > 7:
                warnings.append("Your periods are longer than average - consider discussing with a healthcare provider")
        
        # Next period prediction confidence
        analysis = latest_period.analyze_cycle_regularity()
        reliability = analysis.get('prediction_reliability', 0)
        
        if reliability >= 80:
            insights.append(f"Period predictions are highly reliable ({reliability:.0f}% confidence)")
        elif reliability >= 60:
            insights.append(f"Period predictions are moderately reliable ({reliability:.0f}% confidence)")
        else:
            insights.append(f"Track more cycles to improve prediction accuracy (currently {reliability:.0f}%)")
        
        return Response({
            'status': 'success',
            'data': {
                'insights': insights,
                'warnings': warnings,
                'cycles_analyzed': periods.count(),
                'prediction_confidence': reliability
            }
        })

    @action(detail=False, methods=['get'])
    def cycle_analysis(self, request):
        """Get cycle analysis based on request role."""
        from datetime import date
        
        # Check both query params and headers for role
        role = request.query_params.get('role') or request.headers.get('role', 'self')
        periods = self.get_queryset().order_by('-start_date')
        
        if not periods.exists():
            return Response({
                'error': 'No periods found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        latest_period = periods.first()
        
        # Get user profile for gender
        try:
            profile = request.user.userprofile
            gender = profile.sex or 'none'
        except:
            gender = 'none'
        
        # Calculate current status
        today = date.today()
        current_status = self._calculate_current_status(latest_period, today, gender)
        
        # For non-female users, check if they have a partner to track
        if gender != 'female':
            # Check if user has a partner
            try:
                user_profile = request.user.userprofile
                partners = user_profile.partners.all()
                
                if partners.exists():
                    # Get partner's period data
                    partner = partners.first()
                    partner_user = partner.user
                    partner_periods = Period.objects.filter(user=partner_user).order_by('-start_date')
                    
                    if partner_periods.exists():
                        partner_latest_period = partner_periods.first()
                        partner_analysis = partner_latest_period.analyze_cycle_regularity()
                        
                        # Get partner's gender
                        try:
                            partner_gender = partner_user.userprofile.sex or 'none'
                        except:
                            partner_gender = 'none'
                        
                        # Calculate partner's current status
                        partner_status = self._calculate_current_status(
                            partner_latest_period, today, partner_gender
                        )
                        
                        partner_name = f"{partner_user.first_name} {partner_user.last_name}".strip()
                        if not partner_name:
                            partner_name = partner_user.username
                        
                        return Response({
                            'status': 'success',
                            'data': {
                                'gender': gender,
                                'tracking_mode': 'partner',
                                'partner_info': {
                                    'name': partner_name,
                                    'next_period_date': partner_analysis.get('next_predicted_date'),
                                    'days_until_period': partner_status.get('days_until_next_period'),
                                    'current_phase': partner_status.get('phase'),
                                    'is_on_period': partner_status.get('is_on_period'),
                                    'cycle_regularity': partner_analysis.get('regularity_score'),
                                    'average_cycle_length': partner_analysis.get('average_cycle')
                                },
                                'support_tips': self._get_support_tips(partner_status)
                            },
                            'view_type': 'partner_tracking'
                        })
            except Exception as e:
                print(f"Error fetching partner data: {e}")
            
            # No partner or no partner data
            return Response({
                'status': 'success',
                'data': {
                    'gender': gender,
                    'tracking_mode': 'none',
                    'message': 'Cycle tracking features are designed for female users. Link a partner to track their cycle.',
                    'current_status': current_status
                },
                'view_type': 'self'
            })
        
        # For female users, get full cycle analysis
        analysis = latest_period.analyze_cycle_regularity()
        
        # Add current status to analysis
        enhanced_analysis = {
            **analysis,
            'current_status': current_status,
            'gender': gender
        }
        
        if role == 'partner':
            # Limited data for partners
            partner_data = {
                'next_predicted_date': analysis.get('next_predicted_date'),
                'cycle_length_avg': analysis.get('average_cycle'),
                'is_regular': analysis.get('regularity_score'),
                'last_period_start': latest_period.start_date,
                'current_phase': current_status.get('phase'),
                'days_until_next': current_status.get('days_until_next_period'),
                'partner_name': getattr(request, 'partner_info', {}).get('partner_name'),
                'partner_id': getattr(request, 'partner_info', {}).get('partner_id')
            }
            return Response({
                'status': 'success',
                'data': partner_data,
                'view_type': 'partner'
            })
        
        # Full data for the user themselves
        return Response({
            'status': 'success',
            'data': enhanced_analysis,
            'view_type': 'self'
        })
    
    def _calculate_current_status(self, latest_period, today, gender):
        """Calculate current cycle status with phase information."""
        from datetime import date
        
        # Only calculate cycle phases for females
        if gender != 'female':
            return {
                'is_on_period': False,
                'current_day': None,
                'phase': 'Not applicable',
                'phase_description': 'Cycle tracking is for female users',
                'days_until_next_period': None,
                'is_fertile_window': False
            }
        
        # Calculate if currently on period
        period_end = latest_period.end_date or latest_period.predicted_end_date
        is_on_period = latest_period.start_date <= today <= (period_end or today)
        
        # Calculate current day of period
        current_day = None
        if is_on_period:
            current_day = (today - latest_period.start_date).days + 1
        
        # Calculate days until next period
        next_period_date = latest_period.next_period_start_date or latest_period.calculate_next_period()
        days_until_next = (next_period_date - today).days if next_period_date else None
        
        # Calculate cycle day (day in current cycle)
        cycle_day = None
        cycle_length = latest_period.cycle_length or 28
        if latest_period.start_date <= today:
            cycle_day = (today - latest_period.start_date).days + 1
            # If past cycle length, we're in next cycle
            if cycle_day > cycle_length and next_period_date and today >= next_period_date:
                cycle_day = (today - next_period_date).days + 1
        
        # Determine phase
        phase, phase_description, is_fertile = self._determine_cycle_phase(
            cycle_day, cycle_length, is_on_period, current_day
        )
        
        return {
            'is_on_period': is_on_period,
            'current_day_of_period': current_day,
            'cycle_day': cycle_day,
            'phase': phase,
            'phase_description': phase_description,
            'days_until_next_period': days_until_next,
            'is_fertile_window': is_fertile,
            'cycle_length': cycle_length
        }
    
    def _determine_cycle_phase(self, cycle_day, cycle_length, is_on_period, period_day):
        """Determine which phase of the cycle the user is in."""
        if cycle_day is None:
            return 'Unknown', 'Unable to determine cycle phase', False
        
        # Menstrual Phase (Days 1-5 typically)
        if is_on_period:
            return (
                'Menstrual',
                f'Day {period_day} of your period. Focus on rest and self-care.',
                False
            )
        
        # Follicular Phase (Days 6-13)
        if 6 <= cycle_day <= 13:
            return (
                'Follicular',
                f'Day {cycle_day} of your cycle. Energy levels typically increase during this phase.',
                False
            )
        
        # Ovulation Phase (Days 14-16)
        ovulation_day = cycle_length // 2
        if ovulation_day - 1 <= cycle_day <= ovulation_day + 1:
            return (
                'Ovulation',
                f'Day {cycle_day} of your cycle. You are in your ovulation window.',
                True
            )
        
        # Fertile Window (Days 12-17)
        fertile_start = ovulation_day - 3
        fertile_end = ovulation_day + 2
        if fertile_start <= cycle_day <= fertile_end:
            return (
                'Fertile Window',
                f'Day {cycle_day} of your cycle. You are in your fertile window.',
                True
            )
        
        # Luteal Phase (Days 17-28)
        if cycle_day > fertile_end:
            days_to_period = cycle_length - cycle_day
            if days_to_period <= 3:
                return (
                    'Late Luteal (PMS)',
                    f'Day {cycle_day} of your cycle. PMS symptoms may occur. Period expected in {days_to_period} days.',
                    False
                )
            return (
                'Luteal',
                f'Day {cycle_day} of your cycle. Post-ovulation phase.',
                False
            )
        
        # Default
        return (
            'Cycle Day ' + str(cycle_day),
            f'Day {cycle_day} of your cycle.',
            False
        )
    
    def _get_support_tips(self, partner_status):
        """Provide helpful tips for partners based on cycle phase."""
        phase = partner_status.get('phase', '')
        is_on_period = partner_status.get('is_on_period', False)
        days_until = partner_status.get('days_until_next_period')
        
        tips = []
        
        if is_on_period:
            tips = [
                "Be extra understanding and patient",
                "Offer comfort items like heating pads or favorite snacks",
                "Help with household tasks to reduce stress",
                "Respect their need for rest and space"
            ]
        elif 'PMS' in phase or (days_until and days_until <= 3):
            tips = [
                "PMS symptoms may be present - be patient and supportive",
                "Avoid unnecessary conflicts or stress",
                "Offer emotional support and understanding",
                "Stock up on comfort items they might need"
            ]
        elif 'Ovulation' in phase or 'Fertile' in phase:
            tips = [
                "Energy levels are typically higher during this phase",
                "Good time for activities and quality time together",
                "Be aware if you're planning or avoiding pregnancy"
            ]
        else:
            tips = [
                "Maintain open communication about their needs",
                "Be supportive and understanding throughout the cycle"
            ]
        
        return tips
    

    @action(detail=False, methods=['get'])
    def symptom_patterns(self, request):
        """Analyze symptom patterns across cycles."""
        try:
            profile = request.user.userprofile
            gender = profile.sex or 'none'
        except:
            gender = 'none'
        
        if gender != 'female':
            return Response({
                'error': 'Symptom analysis is only available for female users'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        periods = Period.objects.filter(
            user=request.user,
            symptoms__isnull=False
        ).exclude(symptoms='').order_by('-start_date')[:10]
        
        if not periods.exists():
            return Response({
                'error': 'No symptom data found. Start tracking symptoms to see patterns.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Common symptoms to track
        common_symptoms = [
            'cramps', 'headache', 'bloating', 'fatigue', 'mood swings',
            'back pain', 'nausea', 'breast tenderness', 'acne', 'anxiety',
            'irritability', 'food cravings', 'insomnia'
        ]
        
        symptom_frequency = {}
        for symptom in common_symptoms:
            count = sum(1 for p in periods if symptom.lower() in p.symptoms.lower())
            if count > 0:
                symptom_frequency[symptom] = {
                    'count': count,
                    'percentage': round((count / periods.count()) * 100, 1)
                }
        
        # Sort by frequency
        sorted_symptoms = sorted(
            symptom_frequency.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Generate insights
        insights = []
        if sorted_symptoms:
            most_common = sorted_symptoms[0]
            insights.append(f"Your most common symptom is {most_common[0]} ({most_common[1]['percentage']}% of cycles)")
            
            if len(sorted_symptoms) >= 3:
                top_three = [s[0] for s in sorted_symptoms[:3]]
                insights.append(f"Top symptoms: {', '.join(top_three)}")
        
        return Response({
            'status': 'success',
            'data': {
                'symptom_frequency': dict(sorted_symptoms),
                'total_periods_analyzed': periods.count(),
                'insights': insights
            }
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Period deleted successfully"},
            status=status.HTTP_200_OK
        )
    
class OvulationDetailView(APIView):
    """Viewset for managing Ovulation predictions."""
    permission_classes= [IsAuthenticated]

    def get(self,request ,period_id=None ):
        try:
            if period_id is not None:
                period = Period.objects.get(id=period_id, user=request.user)
            else:
                period = Period.objects.filter(user=request.user).latest("start_date")
                if not period:
                    return Response({"error": "No period data found for the user."}, status=status.HTTP_404_NOT_FOUND)
                
            ovulation, created = Ovulation.objects.get_or_create(period=period, user=request.user)
            serializer = OvulationSerializer(ovulation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ovulation.DoesNotExist:
            return Response({"error": "Ovulation data not found for this period."}, status=status.HTTP_404_NOT_FOUND)
        

class WellnessLogView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WellnessLogSerializer

    def get_queryset(self):
        return WellnessLog.objects.filter(user=self.request.user).order_by('-date')

    def create(self, request, *args, **kwargs):
        user = request.user
        today = timezone.localdate()  # ✅ تاریخ خالص (نه datetime)

        instance, created = WellnessLog.objects.update_or_create(
            user=user,
            date=today,
            defaults=request.data  # داده‌های POST شده
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)



# Notification views moved to notifications app
# Use: from notifications.views import NotificationViewSet, NotificationPreferenceViewSet


class NotificationGeneratorView(APIView):
    """Generate smart notifications based on cycle data."""
    permission_classes = [IsAuthenticated]
    
    def _get_notification_time(self, date, preferences):
        """Helper to create notification datetime from date and preferences."""
        from datetime import datetime, time as datetime_time
        from django.utils import timezone
        
        # Handle preferred_notification_time whether it's a time object or string
        pref_time = preferences.preferred_notification_time
        if isinstance(pref_time, str):
            hour, minute, second = map(int, pref_time.split(':'))
            pref_time = datetime_time(hour, minute, second)
        
        notification_time = datetime.combine(date, pref_time)
        return timezone.make_aware(notification_time)
    
    def post(self, request):
        """Generate notifications for the user."""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        user = request.user
        
        # Get user preferences
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        
        # Get user's gender
        try:
            gender = user.userprofile.sex or 'none'
        except:
            gender = 'none'
        
        notifications_created = []
        
        # For female users - generate cycle notifications
        if gender == 'female':
            periods = Period.objects.filter(user=user).order_by('-start_date')
            
            if periods.exists():
                latest_period = periods.first()
                next_period_date = latest_period.next_period_start_date or latest_period.calculate_next_period()
                
                if next_period_date:
                    today = timezone.now().date()
                    
                    # Period coming notification
                    if preferences.period_reminder_days > 0:
                        reminder_date = next_period_date - timedelta(days=preferences.period_reminder_days)
                        if reminder_date >= today:
                            notification_time = self._get_notification_time(reminder_date, preferences)
                            
                            # Check if notification already exists
                            if not Notification.objects.filter(
                                user=user,
                                notification_type='PERIOD_COMING',
                                scheduled_time__date=reminder_date
                            ).exists():
                                notif = Notification.objects.create(
                                    user=user,
                                    notification_type='PERIOD_COMING',
                                    title='Period Coming Soon',
                                    message=f'Your period is expected in {preferences.period_reminder_days} days. Prepare supplies and plan accordingly.',
                                    scheduled_time=notification_time,
                                    related_period=latest_period
                                )
                                notifications_created.append(notif.notification_type)
                    
                    # PMS phase notification
                    if preferences.pms_phase_alert:
                        pms_start_date = next_period_date - timedelta(days=4)
                        if pms_start_date >= today:
                            notification_time = self._get_notification_time(pms_start_date, preferences)
                            
                            if not Notification.objects.filter(
                                user=user,
                                notification_type='PMS_PHASE',
                                scheduled_time__date=pms_start_date
                            ).exists():
                                notif = Notification.objects.create(
                                    user=user,
                                    notification_type='PMS_PHASE',
                                    title='PMS Phase Starting',
                                    message='You may experience PMS symptoms in the coming days. Practice self-care and be patient with yourself.',
                                    scheduled_time=notification_time,
                                    related_period=latest_period
                                )
                                notifications_created.append(notif.notification_type)
                    
                    # Ovulation notification
                    if preferences.ovulation_alert:
                        cycle_length = latest_period.cycle_length or 28
                        ovulation_date = latest_period.start_date + timedelta(days=cycle_length // 2)
                        
                        if ovulation_date >= today:
                            notification_time = self._get_notification_time(ovulation_date, preferences)
                            
                            if not Notification.objects.filter(
                                user=user,
                                notification_type='OVULATION_COMING',
                                scheduled_time__date=ovulation_date
                            ).exists():
                                notif = Notification.objects.create(
                                    user=user,
                                    notification_type='OVULATION_COMING',
                                    title='Ovulation Window',
                                    message='You are entering your ovulation window. Energy levels are typically highest during this phase.',
                                    scheduled_time=notification_time,
                                    related_period=latest_period
                                )
                                notifications_created.append(notif.notification_type)
                    
                    # Fertile window notification
                    if preferences.fertile_window_alert:
                        cycle_length = latest_period.cycle_length or 28
                        fertile_start = latest_period.start_date + timedelta(days=(cycle_length // 2) - 3)
                        
                        if fertile_start >= today:
                            notification_time = self._get_notification_time(fertile_start, preferences)
                            
                            if not Notification.objects.filter(
                                user=user,
                                notification_type='FERTILE_WINDOW',
                                scheduled_time__date=fertile_start
                            ).exists():
                                notif = Notification.objects.create(
                                    user=user,
                                    notification_type='FERTILE_WINDOW',
                                    title='Fertile Window Starting',
                                    message='You are entering your fertile window. Be aware if planning or avoiding pregnancy.',
                                    scheduled_time=notification_time,
                                    related_period=latest_period
                                )
                                notifications_created.append(notif.notification_type)
        
        # For male users - generate partner notifications
        elif gender == 'male':
            try:
                user_profile = user.userprofile
                partners = user_profile.partners.all()
                
                if partners.exists():
                    partner = partners.first()
                    partner_user = partner.user
                    partner_periods = Period.objects.filter(user=partner_user).order_by('-start_date')
                    
                    if partner_periods.exists():
                        latest_partner_period = partner_periods.first()
                        next_period_date = latest_partner_period.next_period_start_date or latest_partner_period.calculate_next_period()
                        
                        if next_period_date:
                            today = timezone.now().date()
                            
                            # Partner period notification
                            if preferences.partner_period_alert:
                                reminder_date = next_period_date - timedelta(days=1)
                                if reminder_date >= today:
                                    notification_time = self._get_notification_time(reminder_date, preferences)
                                    
                                    if not Notification.objects.filter(
                                        user=user,
                                        notification_type='PARTNER_PERIOD',
                                        scheduled_time__date=reminder_date
                                    ).exists():
                                        partner_name = f"{partner_user.first_name} {partner_user.last_name}".strip() or partner_user.username
                                        notif = Notification.objects.create(
                                            user=user,
                                            notification_type='PARTNER_PERIOD',
                                            title="Partner's Period Coming",
                                            message=f"{partner_name}'s period starts tomorrow. Be extra supportive and understanding.",
                                            scheduled_time=notification_time
                                        )
                                        notifications_created.append(notif.notification_type)
                            
                            # Partner PMS notification
                            if preferences.partner_pms_alert:
                                pms_date = next_period_date - timedelta(days=3)
                                if pms_date >= today:
                                    notification_time = self._get_notification_time(pms_date, preferences)
                                    
                                    if not Notification.objects.filter(
                                        user=user,
                                        notification_type='PARTNER_PMS',
                                        scheduled_time__date=pms_date
                                    ).exists():
                                        partner_name = f"{partner_user.first_name} {partner_user.last_name}".strip() or partner_user.username
                                        notif = Notification.objects.create(
                                            user=user,
                                            notification_type='PARTNER_PMS',
                                            title="Partner's PMS Phase",
                                            message=f"{partner_name} may be experiencing PMS symptoms. Be patient and offer support.",
                                            scheduled_time=notification_time
                                        )
                                        notifications_created.append(notif.notification_type)
            except Exception as e:
                print(f"Error generating partner notifications: {e}")
        
        # Wellness reminder (for all users)
        if preferences.wellness_reminder:
            tomorrow = timezone.now().date() + timedelta(days=1)
            notification_time = self._get_notification_time(tomorrow, preferences)
            
            if not Notification.objects.filter(
                user=user,
                notification_type='WELLNESS_REMINDER',
                scheduled_time__date=tomorrow
            ).exists():
                notif = Notification.objects.create(
                    user=user,
                    notification_type='WELLNESS_REMINDER',
                    title='Log Your Wellness Data',
                    message='Take a moment to log your mood, energy, and other wellness metrics for today.',
                    scheduled_time=notification_time
                )
                notifications_created.append(notif.notification_type)
        
        return Response({
            'status': 'success',
            'message': f'Generated {len(notifications_created)} notifications',
            'notifications_created': notifications_created
        })
