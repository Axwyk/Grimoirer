from django.core.management.base import BaseCommand

from battles.services import calculate_all_stats


class Command(BaseCommand):
    help = 'Calculate player stats and scores for valid, unprocessed battles'

    def handle(self, *args, **options):
        self.stdout.write('Calculating battle stats...')
        count = calculate_all_stats()
        self.stdout.write(self.style.SUCCESS(f'✓ Processed stats for {count} battles'))
