from django.db import models


RANK_TIERS = [
    {'name': 'Hierro 3', 'min_elo': 0, 'color': '#6b7280'},
    {'name': 'Hierro 2', 'min_elo': 100, 'color': '#6b7280'},
    {'name': 'Hierro 1', 'min_elo': 200, 'color': '#6b7280'},
    {'name': 'Bronce 3', 'min_elo': 300, 'color': '#cd7f32'},
    {'name': 'Bronce 2', 'min_elo': 400, 'color': '#cd7f32'},
    {'name': 'Bronce 1', 'min_elo': 500, 'color': '#cd7f32'},
    {'name': 'Plata 3', 'min_elo': 600, 'color': '#c0c0c0'},
    {'name': 'Plata 2', 'min_elo': 700, 'color': '#c0c0c0'},
    {'name': 'Plata 1', 'min_elo': 800, 'color': '#c0c0c0'},
    {'name': 'Oro 3', 'min_elo': 900, 'color': '#fbbf24'},
    {'name': 'Oro 2', 'min_elo': 1000, 'color': '#fbbf24'},
    {'name': 'Oro 1', 'min_elo': 1100, 'color': '#fbbf24'},
    {'name': 'Platino 3', 'min_elo': 1200, 'color': '#06b6d4'},
    {'name': 'Platino 2', 'min_elo': 1300, 'color': '#06b6d4'},
    {'name': 'Platino 1', 'min_elo': 1400, 'color': '#06b6d4'},
    {'name': 'Diamante 3', 'min_elo': 1500, 'color': '#a78bfa'},
    {'name': 'Diamante 2', 'min_elo': 1600, 'color': '#a78bfa'},
    {'name': 'Diamante 1', 'min_elo': 1700, 'color': '#a78bfa'},
    {'name': 'Maestro', 'min_elo': 1800, 'color': '#f472b6'},
    {'name': 'Gran Maestro', 'min_elo': 2000, 'color': '#ef4444'},
]

DEFAULT_ELO = 600


def get_rank_tier(elo):
    for tier in reversed(RANK_TIERS):
        if elo >= tier['min_elo']:
            return tier
    return RANK_TIERS[0]


class Rating(models.Model):
    player = models.OneToOneField(
        'players.Player', on_delete=models.CASCADE, related_name='rating'
    )
    elo = models.IntegerField(default=DEFAULT_ELO)
    peak_elo = models.IntegerField(default=DEFAULT_ELO)
    total_battles = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-elo']

    def __str__(self):
        return f'{self.player.name}: {self.elo} ELO'

    @property
    def rank_tier(self):
        return get_rank_tier(self.elo)
