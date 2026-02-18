from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Run complete ML pipeline with feedback"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting ML Pipeline...")

        # Step 1: Generate synthetic dataset
        self.stdout.write("1. Generating synthetic dataset...")
        call_command('generate_synthetic_dataset')

        # Step 2: Train AI model (XGB + Transformer) with feedback
        self.stdout.write("2. Training ML model...")
        call_command('train_ai_model')

        self.stdout.write(self.style.SUCCESS("✅ ML pipeline completed successfully!"))
