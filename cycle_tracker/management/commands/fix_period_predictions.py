from django.core.management.base import BaseCommand
from cycle_tracker.models import Period
from datetime import timedelta

class Command(BaseCommand):
    help = 'Fix incorrect next_period_start_date calculations for existing periods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all periods ordered by user and start_date
        periods = Period.objects.all().order_by('user', '-start_date')
        
        fixed_count = 0
        total_count = 0
        
        for period in periods:
            total_count += 1
            old_next_date = period.next_period_start_date
            
            # Recalculate using smart method
            new_next_date = period.calculate_smart_next_period()
            
            # Check if the date changed significantly (more than 7 days difference)
            if old_next_date and new_next_date:
                days_diff = abs((new_next_date - old_next_date).days)
                if days_diff > 7:
                    self.stdout.write(
                        f'Period ID {period.id} (User: {period.user.username}): '
                        f'{old_next_date} -> {new_next_date} (diff: {days_diff} days)'
                    )
                    
                    if not dry_run:
                        period.next_period_start_date = new_next_date
                        period.save(update_fields=['next_period_start_date'])
                    
                    fixed_count += 1
            elif not old_next_date and new_next_date:
                self.stdout.write(
                    f'Period ID {period.id} (User: {period.user.username}): '
                    f'NULL -> {new_next_date}'
                )
                
                if not dry_run:
                    period.next_period_start_date = new_next_date
                    period.save(update_fields=['next_period_start_date'])
                
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would fix {fixed_count} out of {total_count} periods'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fixed {fixed_count} out of {total_count} periods'
                )
            )