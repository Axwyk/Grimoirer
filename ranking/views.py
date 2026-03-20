from rest_framework.decorators import api_view
from rest_framework.response import Response

from ranking.models import Rating, RANK_TIERS
from ranking.serializers import RatingSerializer
from battles.models import PlayerBattleStats, ALBION_RENDER_URL


@api_view(['GET'])
def ranking_list(request):
    """GET /api/ranking/ — Top 100 players by ELO."""
    from django.conf import settings as django_settings
    qs = Rating.objects.select_related('player').order_by('-elo')
    tracked = getattr(django_settings, 'TRACKED_GUILD', None)
    if tracked:
        qs = qs.filter(player__guild_name=tracked)
    serializer = RatingSerializer(qs[:100], many=True)
    return Response(serializer.data)


@api_view(['GET'])
def player_battle_history(request, player_id):
    """GET /api/players/{id}/stats/ — Player's battle history with scores."""
    stats = (
        PlayerBattleStats.objects
        .filter(player_id=player_id)
        .select_related('battle', 'player')
        .order_by('-battle__start_time')
    )
    data = []
    for s in stats:
        data.append({
            'battle_id': s.battle_id,
            'zone': s.battle.zone,
            'date': s.battle.start_time,
            'total_players': s.battle.total_players,
            'damage_done': s.damage_done,
            'healing_done': s.healing_done,
            'kills': s.kills,
            'deaths': s.deaths,
            'assists': s.assists,
            'kill_fame': s.kill_fame,
            'average_item_power': s.average_item_power,
            'main_weapon': s.main_weapon,
            'role': s.role,
            'weapon_icon': ALBION_RENDER_URL.format(item_id=s.main_weapon) if s.main_weapon else None,
            'raw_score': round(s.raw_score, 2),
            'normalized_score': round(s.normalized_score, 2),
            'elo_before': s.elo_before,
            'elo_after': s.elo_after,
            'elo_change': s.elo_change,
        })
    return Response(data)


@api_view(['GET'])
def ranking_overview(request):
    """GET /api/stats/ — Global stats overview."""
    from django.conf import settings as django_settings
    from players.models import Player
    from battles.models import Battle
    from events.models import Event

    tracked = getattr(django_settings, 'TRACKED_GUILD', None)
    players_qs = Player.objects.all()
    ratings_qs = Rating.objects.all()
    if tracked:
        players_qs = players_qs.filter(guild_name=tracked)
        ratings_qs = ratings_qs.filter(player__guild_name=tracked)

    return Response({
        'total_players': players_qs.count(),
        'total_battles': Battle.objects.filter(is_valid=True).count(),
        'total_events': Event.objects.count(),
        'ranked_players': ratings_qs.count(),
        'tracked_guild': tracked,
        'rank_tiers': RANK_TIERS,
    })
