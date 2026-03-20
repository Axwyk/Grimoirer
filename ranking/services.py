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

    player_stats = list(battle.player_stats.select_related('player'))

    # Calcular percentiles de score normalizado
    norm_scores = [ps.normalized_score for ps in player_stats]
    sorted_scores = sorted(norm_scores)
    n = len(sorted_scores)
    def get_percentile(score):
        # Percentil empírico (proporción de scores menores)
        below = sum(1 for s in sorted_scores if s < score)
        return below / n if n > 1 else 0.5

    P_NEUTRAL = 0.25  # percentil a partir del cual no se pierde ELO

    # Cap dinámico según tamaño de batalla
    def get_cap(n):
        if n >= 20:
            return 31
        elif n >= 10:
            return 24
        elif n >= 6:
            return 18
        else:
            return 12

    cap = get_cap(n)

    for ps in player_stats:
        rating, _ = Rating.objects.get_or_create(
            player=ps.player,
            defaults={'elo': DEFAULT_ELO, 'peak_elo': DEFAULT_ELO},
        )

        ps.elo_before = rating.elo
        k = get_k_factor(rating.total_battles)
        percentile = get_percentile(ps.normalized_score)
        raw_score = ps.raw_score if hasattr(ps, 'raw_score') else 0
        # Lógica robusta:
        if raw_score > 0:
            # Si tiene muertes, gana menos ELO, pero nunca puede perder si aportó
            if ps.deaths > 0:
                elo_change = round((percentile - P_NEUTRAL) / (1 - P_NEUTRAL) * cap * 0.5)
                elo_change = max(0, elo_change)  # Nunca negativo si aportó
            else:
                elo_change = round((percentile - P_NEUTRAL) / (1 - P_NEUTRAL) * cap)
                elo_change = max(0, elo_change)  # Nunca negativo si aportó
            elo_change = min(cap, elo_change)
        elif ps.deaths > 0:
            # Si no aportó y murió, pierde el máximo permitido
            elo_change = max(-k, -cap)
        else:
            # No aportó ni murió, score y ELO deben ser 0 y neutro
            ps.normalized_score = 0
            ps.raw_score = 0
            elo_change = 0

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
    logger.info(f'ELO updated for battle {battle.id} ({len(player_stats)} players)')


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
