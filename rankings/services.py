"""Service layer: auto-scores performance and updates Elo ratings."""

from django.db import transaction
from .models import Player, PlayerElo, FightParticipant
from .elo import auto_score_performance, calculate_elo_change


def _compute_fight_averages(participants_data):
    """Compute average stats across all participants for normalization."""
    fields = ["kill_fame", "deaths", "healing_done", "damage_done", "assists"]
    totals = {f: 0 for f in fields}
    count = len(participants_data) or 1
    for p in participants_data:
        for f in fields:
            totals[f] += p.get(f, 0)
    return {f: totals[f] / count for f in fields}


@transaction.atomic
def process_fight(fight, participants_data):
    """
    Create fight participants, auto-score performance, and update Elo.

    1. Compute fight-wide averages for normalization
    2. Auto-score each participant based on their role
    3. Calculate Elo change purely from performance score
    4. Update PlayerElo records
    """
    fight_avg = _compute_fight_averages(participants_data)

    participants = []
    for p_data in participants_data:
        player = p_data["player"]
        role = p_data["role"]

        player_elo, _ = PlayerElo.objects.get_or_create(
            player=player, role=role, defaults={"elo": 1200, "peak_elo": 1200}
        )

        stats = {
            "kill_fame": p_data.get("kill_fame", 0),
            "deaths": p_data.get("deaths", 0),
            "healing_done": p_data.get("healing_done", 0),
            "damage_done": p_data.get("damage_done", 0),
            "assists": p_data.get("assists", 0),
        }

        perf_score = auto_score_performance(role, stats, fight_avg)

        participant = FightParticipant.objects.create(
            fight=fight,
            player=player,
            role=role,
            performance_score=perf_score,
            elo_before=player_elo.elo,
            **stats,
        )
        participants.append((participant, player_elo))

    # Update Elo for each participant
    for participant, player_elo in participants:
        elo_change = calculate_elo_change(
            player_elo.elo,
            player_elo.total_games,
            float(participant.performance_score),
        )

        player_elo.elo += elo_change
        player_elo.total_games += 1
        if player_elo.elo > player_elo.peak_elo:
            player_elo.peak_elo = player_elo.elo
        player_elo.save()

        participant.elo_after = player_elo.elo
        participant.save(update_fields=["elo_after"])
