from django.core.management.base import BaseCommand

from ranking.services import update_all_elo


class Command(BaseCommand):
    help = 'Update ELO ratings based on processed battle stats'

    def handle(self, *args, **options):
        self.stdout.write('Updating ELO ratings...')
        count = update_all_elo()
        self.stdout.write(self.style.SUCCESS(f'✓ Updated ELO for {count} battles'))
