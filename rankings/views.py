from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Player, PlayerElo, Fight, FightParticipant, Role
from .elo import get_rank, RANK_TIERS
from .serializers import (
    PlayerSerializer,
    PlayerEloSerializer,
    FightSerializer,
    FightCreateSerializer,
)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.prefetch_related("elos").all()
    serializer_class = PlayerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "guild"]
    ordering_fields = ["name", "created_at"]


class FightViewSet(viewsets.ModelViewSet):
    queryset = Fight.objects.prefetch_related(
        "participants", "participants__player"
    ).all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["date", "created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return FightCreateSerializer
        return FightSerializer


@api_view(["GET"])
def leaderboard(request, role):
    """Get leaderboard for a specific role."""
    role = role.upper()
    if role not in Role.values:
        return Response(
            {"error": f"Rol inválido. Opciones: {', '.join(Role.values)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    elos = (
        PlayerElo.objects.filter(role=role)
        .select_related("player")
        .order_by("-elo")
    )

    serializer = PlayerEloSerializer(elos, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def player_history(request, player_id):
    """Get fight history for a player with Elo changes."""
    participations = (
        FightParticipant.objects.filter(player_id=player_id)
        .select_related("fight", "player")
        .order_by("-fight__date")
    )

    data = []
    for p in participations:
        data.append(
            {
                "fight_id": p.fight_id,
                "fight_title": p.fight.title,
                "fight_date": p.fight.date,
                "role": p.role,
                "role_display": p.get_role_display(),
                "performance_score": str(p.performance_score),
                "elo_before": p.elo_before,
                "elo_after": p.elo_after,
                "elo_change": p.elo_after - p.elo_before,
                "rank_name": get_rank(p.elo_after)["name"],
                "rank_color": get_rank(p.elo_after)["color"],
                "kill_fame": p.kill_fame,
                "deaths": p.deaths,
                "healing_done": p.healing_done,
                "damage_done": p.damage_done,
                "assists": p.assists,
            }
        )

    return Response(data)


@api_view(["GET"])
def stats_overview(request):
    """General statistics overview."""
    total_players = Player.objects.count()
    total_fights = Fight.objects.count()
    role_stats = {}
    for role_value, role_label in Role.choices:
        elos = PlayerElo.objects.filter(role=role_value)
        role_stats[role_value] = {
            "label": role_label,
            "total_players": elos.count(),
            "top_player": None,
        }
        top = elos.select_related("player").first()
        if top:
            rank = get_rank(top.elo)
            role_stats[role_value]["top_player"] = {
                "name": top.player.name,
                "elo": top.elo,
                "rank_name": rank["name"],
                "rank_color": rank["color"],
            }

    return Response(
        {
            "total_players": total_players,
            "total_fights": total_fights,
            "roles": role_stats,
            "rank_tiers": RANK_TIERS,
        }
    )
