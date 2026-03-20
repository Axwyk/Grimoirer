from django.core.management.base import BaseCommand

from events.services import fetch_and_store_events, fetch_guild_battles
from battles.services import group_battles, calculate_all_stats
from ranking.services import update_all_elo


class Command(BaseCommand):
    help = 'Run full pipeline: fetch_guild_battles → fetch_events → group → stats → elo'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=51,
                            help='Events per page (max 51)')
        parser.add_argument('--pages', type=int, default=5,
                            help='Max pages to fetch')
        parser.add_argument('--battle-pages', type=int, default=3,
                            help='Max pages of guild battles to fetch')

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=' * 50))
        self.stdout.write(self.style.HTTP_INFO('  ALBION ZvZ RANKING PIPELINE'))
        self.stdout.write(self.style.HTTP_INFO('=' * 50))

        # Step 1: Fetch guild battles from battles API
        self.stdout.write('\n[1/5] Fetching guild battles from Albion API...')
        new_battles, battle_events = fetch_guild_battles(
            limit=20,
            max_pages=options['battle_pages'],
        )
        self.stdout.write(f'  → {new_battles} new battles, {battle_events} events from battles API')

        # Step 2: Fetch events (guild-filtered)
        self.stdout.write('\n[2/5] Fetching guild events from Albion API...')
        events = fetch_and_store_events(
            limit=options['limit'],
            max_pages=options['pages'],
        )
        self.stdout.write(f'  → {events} new events stored')

        # Step 3: Group into battles
        self.stdout.write('\n[3/5] Grouping events into battles...')
        battles = group_battles()
        self.stdout.write(f'  → {battles} new battles created')

        # Step 4: Calculate stats
        self.stdout.write('\n[4/5] Calculating player stats...')
        stats = calculate_all_stats()
        self.stdout.write(f'  → {stats} battles processed')

        # Step 5: Update ELO
        self.stdout.write('\n[5/5] Updating ELO ratings...')
        elo = update_all_elo()
        self.stdout.write(f'  → {elo} battles ELO updated')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Pipeline complete!'))
