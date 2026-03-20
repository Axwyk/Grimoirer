import time
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.services import fetch_and_store_events, fetch_guild_battles
from battles.services import group_battles, calculate_all_stats
from ranking.services import update_all_elo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-fetch new battles and update ELO periodically'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=300,
                            help='Seconds between each cycle (default: 300 = 5 min)')
        parser.add_argument('--once', action='store_true',
                            help='Run once and exit (no loop)')

    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']

        self.stdout.write(self.style.HTTP_INFO('=== Auto-Update Service ==='))
        self.stdout.write(f'Interval: {interval}s | Mode: {"single run" if once else "loop"}')

        while True:
            try:
                self._run_cycle()
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nStopped by user'))
                break
            except Exception as e:
                logger.exception('Error in auto-update cycle')
                self.stdout.write(self.style.ERROR(f'Error: {e}'))

            if once:
                break

            self.stdout.write(f'Next cycle in {interval}s...\n')
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nStopped by user'))
                break

    def _run_cycle(self):
        now = timezone.now().strftime('%H:%M:%S')
        self.stdout.write(f'\n[{now}] Running update cycle...')

        # 1. Fetch guild battles
        new_battles, battle_events = fetch_guild_battles(limit=20, max_pages=3)
        self.stdout.write(f'  Battles: {new_battles} new, {battle_events} events')

        # 2. Fetch events
        events = fetch_and_store_events(limit=51, max_pages=5)
        self.stdout.write(f'  Events: {events} new')

        # 3. Group into battles
        battles = group_battles()
        self.stdout.write(f'  Grouped: {battles} battles')

        # 4. Calculate stats
        stats = calculate_all_stats()
        self.stdout.write(f'  Stats: {stats} processed')

        # 5. Update ELO
        elo = update_all_elo()
        self.stdout.write(f'  ELO: {elo} updated')

        self.stdout.write(self.style.SUCCESS(f'  Cycle complete'))
