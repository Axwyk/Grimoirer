from django.core.management.base import BaseCommand

from battles.services import group_battles


class Command(BaseCommand):
    help = 'Group ungrouped events into battles by zone + temporal proximity'

    def handle(self, *args, **options):
        self.stdout.write('Grouping events into battles...')
        count = group_battles()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} new battles'))
