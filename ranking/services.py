import logging

from django.conf import settings
from django.db import transaction

from battles.models import Battle, PlayerBattleStats
from ranking.models import Rating, DEFAULT_ELO

logger = logging.getLogger(__name__)


def get_k_factor(total_battles):
    """K-factor decrece con la experiencia del jugador."""
    if total_battles < 10:
        return 40
    elif total_battles < 30:
        return 30
    return 20


@transaction.atomic
def update_elo_for_battle(battle):
    """
    Actualiza ELO de todos los jugadores en una battle procesada.
    Usa normalized_score (z-score) para determinar ganancia/pérdida.
    """
    if battle.elo_updated or not battle.processed:
        return

    player_stats = battle.player_stats.select_related('player')

    for ps in player_stats:
        rating, _ = Rating.objects.get_or_create(
            player=ps.player,
            defaults={'elo': DEFAULT_ELO, 'peak_elo': DEFAULT_ELO},
        )

        ps.elo_before = rating.elo

        k = get_k_factor(rating.total_battles)

        # Clamp normalized_score a [-3, 3] para evitar cambios extremos
        norm = max(-3.0, min(3.0, ps.normalized_score))

        # Cambio ELO: K * norm / 3 → máximo cambio = ±K, cap en ±31
        elo_change = round(k * norm / 3)
        elo_change = max(-k, min(31, elo_change))

        rating.elo = max(0, rating.elo + elo_change)
        rating.total_battles += 1
        if rating.elo > rating.peak_elo:
            rating.peak_elo = rating.elo
        rating.save()

        ps.elo_after = rating.elo
        ps.elo_change = elo_change
        ps.save(update_fields=['elo_before', 'elo_after', 'elo_change'])

    battle.elo_updated = True
    battle.save(update_fields=['elo_updated'])
    logger.info(f'ELO updated for battle {battle.id} ({player_stats.count()} players)')


def update_all_elo():
    """Actualiza ELO para todas las battles procesadas pendientes."""
    battles = Battle.objects.filter(
        processed=True, elo_updated=False
    ).order_by('start_time')

    count = 0
    for battle in battles:
        update_elo_for_battle(battle)
        count += 1
    return count
