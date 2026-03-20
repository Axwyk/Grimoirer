from django.core.management.base import BaseCommand

from events.services import fetch_and_store_events


class Command(BaseCommand):
    help = 'Fetch latest kill events from Albion Online API'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=51,
                            help='Events per page (max 51)')
        parser.add_argument('--pages', type=int, default=5,
                            help='Max pages to fetch')

    def handle(self, *args, **options):
        self.stdout.write('Fetching events from Albion API...')
        count = fetch_and_store_events(
            limit=options['limit'],
            max_pages=options['pages'],
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Stored {count} new events'))
