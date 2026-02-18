from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cycle_tracker.models import Period
from notifications.models import Notification, NotificationPreference
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generate smart notifications for all users based on their cycle data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate notifications for specific user ID only',
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=14,
            help='Generate notifications for X days ahead (default: 14)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed debug information',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create notifications even if they exist today',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        days_ahead = options.get('days_ahead')
        self.verbose = options.get('verbose', False)
        self.force = options.get('force', False)

        if user_id:
            users = User.objects.filter(id=user_id)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            users = User.objects.all()

        total_notifications = 0
        users_processed = 0

        for user in users:
            try:
                count = self.generate_user_notifications(user, days_ahead)
                total_notifications += count
                users_processed += 1
                
                if count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Generated {count} notifications for {user.username}'
                        )
                    )
                elif self.verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f'○ No notifications for {user.username}'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error for {user.username}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Complete! Generated {total_notifications} notifications for {users_processed} users'
            )
        )

    def generate_user_notifications(self, user, days_ahead):
        """Generate notifications for a single user."""
        notifications_created = 0
        
        # Get or create preferences
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        
        # Get user's gender
        try:
            gender = user.userprofile.sex or 'none'
        except:
            gender = 'none'
        
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        if self.verbose:
            self.stdout.write(f'\n--- {user.username} (gender: {gender}) ---')
        
        # For female users
        if gender == 'female':
            periods = Period.objects.filter(user=user).order_by('-start_date')
            
            if self.verbose:
                self.stdout.write(f'  Periods found: {periods.count()}')
            
            if periods.exists():
                latest_period = periods.first()
                next_period_date = latest_period.next_period_start_date or latest_period.calculate_next_period()
                
                if self.verbose:
                    self.stdout.write(f'  Latest period: {latest_period.start_date}')
                    self.stdout.write(f'  Next period: {next_period_date}')
                    self.stdout.write(f'  Today: {today}, Future date: {future_date}')
                
                if next_period_date:
                    days_until_period = (next_period_date - today).days
                    
                    if self.verbose:
                        self.stdout.write(f'  Days until period: {days_until_period}')
                    
                    # Period reminder notification (if within reminder window)
                    reminder_days = preferences.reminder_days_before
                    if self.verbose:
                        self.stdout.write(f'  Reminder days setting: {reminder_days}')
                    
                    if 0 < days_until_period <= reminder_days:
                        if self.verbose:
                            self.stdout.write(f'  Creating period reminder...')
                        if self.create_notification(
                            user, 'period_reminder', 
                            'Period Coming Soon',
                            f'Your period is expected in {days_until_period} days on {next_period_date.strftime("%B %d")}.',
                            related_id=latest_period.id,
                            related_type='period'
                        ):
                            notifications_created += 1
                            if self.verbose:
                                self.stdout.write(f'  ✓ Period reminder created')
                        elif self.verbose:
                            self.stdout.write(f'  ✗ Period reminder already exists')
                    
                    # Period approaching (1 day before)
                    if days_until_period == 1:
                        if self.create_notification(
                            user, 'period_approaching',
                            'Period Tomorrow',
                            'Your period is expected to start tomorrow. Be prepared!',
                            related_id=latest_period.id,
                            related_type='period'
                        ):
                            notifications_created += 1
                    
                    # PMS warning (3-4 days before)
                    if 3 <= days_until_period <= 4:
                        if self.create_notification(
                            user, 'pms_warning',
                            'PMS Phase',
                            'You may experience PMS symptoms. Practice self-care and stress management.',
                            related_id=latest_period.id,
                            related_type='period'
                        ):
                            notifications_created += 1
                    
                    # Ovulation notification
                    cycle_length = latest_period.cycle_length or 28
                    cycle_day = (today - latest_period.start_date).days
                    ovulation_day = cycle_length // 2
                    
                    if self.verbose:
                        self.stdout.write(f'  Cycle day: {cycle_day}, Ovulation day: {ovulation_day}')
                    
                    # Ovulation window (day 12-16 of cycle)
                    if 12 <= cycle_day <= 16:
                        if self.create_notification(
                            user, 'ovulation',
                            'Ovulation Window',
                            f'You are in your ovulation window (Day {cycle_day} of your cycle).',
                            related_id=latest_period.id,
                            related_type='period'
                        ):
                            notifications_created += 1
                    
                    # Fertile window (day 10-17 of cycle)
                    if 10 <= cycle_day <= 17:
                        if self.create_notification(
                            user, 'fertile_window',
                            'Fertile Window',
                            'You are in your fertile window. Track your symptoms.',
                            related_id=latest_period.id,
                            related_type='period'
                        ):
                            notifications_created += 1
        
        # For male users with partners
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
                            partner_name = f"{partner_user.first_name} {partner_user.last_name}".strip() or partner_user.username
                            days_until_partner_period = (next_period_date - today).days
                            
                            if self.verbose:
                                self.stdout.write(f'  Partner period in: {days_until_partner_period} days')
                            
                            # Partner period notification (1-2 days before)
                            if 1 <= days_until_partner_period <= 2:
                                if self.verbose:
                                    self.stdout.write(f'  Creating partner period notification...')
                                if self.create_notification(
                                    user, 'partner_message',
                                    "Partner's Period Coming",
                                    f"{partner_name}'s period starts in {days_until_partner_period} day(s). Be supportive!",
                                    related_id=partner_user.id,
                                    related_type='partner'
                                ):
                                    notifications_created += 1
                                    if self.verbose:
                                        self.stdout.write(f'  ✓ Partner notification created')
                                elif self.verbose:
                                    self.stdout.write(f'  ✗ Partner notification already exists')
                            
                            # Partner PMS notification (3-4 days before)
                            if 3 <= days_until_partner_period <= 4:
                                if self.create_notification(
                                    user, 'partner_message',
                                    "Partner's PMS Phase",
                                    f"{partner_name} may be experiencing PMS symptoms. Extra care and understanding appreciated!",
                                    related_id=partner_user.id,
                                    related_type='partner'
                                ):
                                    notifications_created += 1
            except Exception as e:
                pass
        
        # Wellness reminder (all users) - only if they haven't logged today
        from cycle_tracker.models import WellnessLog
        today_log = WellnessLog.objects.filter(user=user, date=today).exists()
        
        if not today_log:
            if self.create_notification(
                user, 'wellness_reminder',
                'Log Your Wellness',
                'Take a moment to log your wellness metrics for today.',
            ):
                notifications_created += 1
        
        return notifications_created

    def create_notification(self, user, notif_type, title, message, related_id=None, related_type=None):
        """Create a notification if it doesn't already exist."""
        today = timezone.now().date()
        
        # Check if similar notification already exists today (unless force mode)
        if not self.force:
            if Notification.objects.filter(
                user=user,
                notification_type=notif_type,
                title=title,
                created_at__date=today
            ).exists():
                return False
        
        Notification.objects.create(
            user=user,
            notification_type=notif_type,
            title=title,
            message=message,
            related_id=related_id,
            related_type=related_type
        )
        return True
