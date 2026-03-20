# Script para recalcular todas las batallas y ELO en Grimoirer

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from battles.models import Battle, PlayerBattleStats
from battles.services import calculate_battle_stats
from ranking.models import Rating
from ranking.services import update_all_elo

print('Eliminando PlayerBattleStats...')
PlayerBattleStats.objects.all().delete()
print('Reseteando batallas procesadas...')
Battle.objects.filter(processed=True).update(processed=False)
print('Calculando stats de batallas válidas...')
for b in Battle.objects.filter(is_valid=True):
    calculate_battle_stats(b)
print('Reseteando flags de ELO...')
Battle.objects.filter(elo_updated=True).update(elo_updated=False)
print('Reseteando ELO de todos los jugadores...')
Rating.objects.all().update(elo=600, peak_elo=600, total_battles=0)
print('Actualizando ELO...')
count = update_all_elo()
print(f'Recalculated {count} battles')
