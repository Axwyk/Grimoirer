"""
Elo rating engine for ZvZ roaming fights in Albion Online.

Automatic performance-based system:
- Rating changes are based purely on individual performance, NOT win/loss
- Each role is scored using role-specific metrics
- K-factor adjusts based on number of games played
- Rank tiers from Hierro to Gran Maestro
"""

import math

# ─── Rank tiers ───────────────────────────────────────────────────────

RANK_TIERS = [
    {"name": "Hierro",       "min_elo": 0,    "color": "#6b7280"},
    {"name": "Bronce",       "min_elo": 900,  "color": "#cd7f32"},
    {"name": "Plata",        "min_elo": 1100, "color": "#c0c0c0"},
    {"name": "Oro",          "min_elo": 1300, "color": "#fbbf24"},
    {"name": "Platino",      "min_elo": 1500, "color": "#06b6d4"},
    {"name": "Diamante",     "min_elo": 1700, "color": "#a78bfa"},
    {"name": "Maestro",      "min_elo": 1900, "color": "#f472b6"},
    {"name": "Gran Maestro", "min_elo": 2100, "color": "#ef4444"},
]


def get_rank(elo: int) -> dict:
    """Return the rank tier dict for a given Elo."""
    rank = RANK_TIERS[0]
    for tier in RANK_TIERS:
        if elo >= tier["min_elo"]:
            rank = tier
    return rank


# ─── Auto-performance scoring per role ────────────────────────────────

def _safe_ratio(a, b, default=0.0):
    return a / b if b > 0 else default


def score_tank(stats: dict, fight_avg: dict) -> float:
    """
    Tanks scored on: low deaths, high assists, survival.
    Returns 0-10.
    """
    avg_deaths = fight_avg.get("deaths", 1)
    avg_assists = fight_avg.get("assists", 1)

    # Survival score: fewer deaths = better (inverted, capped)
    death_score = max(0, 10 - (stats["deaths"] / max(avg_deaths, 0.5)) * 5)
    # Assist contribution
    assist_score = min(10, (stats["assists"] / max(avg_assists, 0.5)) * 5)
    # Damage taken proxy: kill_fame as a proxy for engagement
    engagement = min(10, (stats["kill_fame"] / max(fight_avg.get("kill_fame", 1), 1)) * 5)

    return min(10.0, (death_score * 0.40 + assist_score * 0.65 + engagement * 0.25))


def score_healer(stats: dict, fight_avg: dict) -> float:
    """
    Healers scored on: high healing, low deaths, assists.
    Returns 0-10.
    """
    avg_healing = fight_avg.get("healing_done", 1)
    avg_deaths = fight_avg.get("deaths", 1)

    healing_score = min(10, (stats["healing_done"] / max(avg_healing, 0.5)) * 5)
    death_score = max(0, 10 - (stats["deaths"] / max(avg_deaths, 0.5)) * 5)
    assist_score = min(10, (stats["assists"] / max(fight_avg.get("assists", 1), 0.5)) * 5)

    return min(10.0, (healing_score * 0.50 + death_score * 0.30 + assist_score * 0.20))


def score_support(stats: dict, fight_avg: dict) -> float:
    """
    Supports scored on: assists, healing, low deaths.
    Returns 0-10.
    """
    avg_assists = fight_avg.get("assists", 1)
    avg_healing = fight_avg.get("healing_done", 1)
    avg_deaths = fight_avg.get("deaths", 1)

    assist_score = min(10, (stats["assists"] / max(avg_assists, 0.5)) * 5)
    healing_score = min(10, (stats["healing_done"] / max(avg_healing, 0.5)) * 5)
    death_score = max(0, 10 - (stats["deaths"] / max(avg_deaths, 0.5)) * 5)
    damage_score = min(10, (stats["damage_done"] / max(fight_avg.get("damage_done", 1), 1)) * 5)

    return min(10.0, (assist_score * 0.45 + healing_score * 0.35 + death_score * 0.25 + damage_score * 0.15))


def score_dps(stats: dict, fight_avg: dict) -> float:
    """
    DPS scored on: high damage, high kill fame, low deaths.
    Returns 0-10.
    """
    avg_damage = fight_avg.get("damage_done", 1)
    avg_kill_fame = fight_avg.get("kill_fame", 1)
    avg_deaths = fight_avg.get("deaths", 1)

    damage_score = min(10, (stats["damage_done"] / max(avg_damage, 0.5)) * 5)
    kill_score = min(10, (stats["kill_fame"] / max(avg_kill_fame, 0.5)) * 5)
    death_score = max(0, 10 - (stats["deaths"] / max(avg_deaths, 0.5)) * 5)
    assist_score = min(10, (stats["assists"] / max(fight_avg.get("assists", 1), 0.5)) * 5)

    return min(10.0, (damage_score * 0.50 + kill_score * 0.60 + death_score * 0.20 + assist_score * 0.15))


ROLE_SCORERS = {
    "TANK": score_tank,
    "HEALER": score_healer,
    "SUPPORT": score_support,
    "DPS": score_dps,
}


def auto_score_performance(role: str, stats: dict, fight_avg: dict) -> float:
    """
    Automatically calculate performance score (0-10) based on role and stats.
    Compares the player's stats against the fight averages.
    """
    scorer = ROLE_SCORERS.get(role, score_dps)
    score = scorer(stats, fight_avg)
    return round(max(0.0, min(10.0, score)), 1)


# ─── Elo calculation ─────────────────────────────────────────────────

def get_k_factor(games_played: int) -> int:
    """Higher K for new players, lower for established ones."""
    if games_played < 10:
        return 48
    if games_played < 30:
        return 32
    return 24


def calculate_elo_change(
    player_elo: int,
    games_played: int,
    performance_score: float,
) -> int:
    """
    Calculate Elo change based purely on performance.

    Performance score 0-10 maps to Elo change:
    - 5.0 = neutral (0 change, baseline "average" performance)
    - 10.0 = max gain
    - 0.0 = max loss

    The K-factor scales the magnitude.
    """
    k = get_k_factor(games_played)
    # Map 0-10 to -1..+1: score 5 = 0, score 10 = +1, score 0 = -1
    normalized = (performance_score - 5.0) / 5.0
    change = k * normalized
    return round(change)
