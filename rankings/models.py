from django.db import models


class Role(models.TextChoices):
    TANK = "TANK", "Tanque"
    HEALER = "HEALER", "Healer"
    SUPPORT = "SUPPORT", "Soporte"
    DPS = "DPS", "DPS"


class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    guild = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlayerElo(models.Model):
    """Elo rating per player per role."""

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="elos")
    role = models.CharField(max_length=10, choices=Role.choices)
    elo = models.IntegerField(default=1200)
    total_games = models.PositiveIntegerField(default=0)
    peak_elo = models.IntegerField(default=1200)

    class Meta:
        unique_together = ("player", "role")
        ordering = ["-elo"]

    def __str__(self):
        return f"{self.player.name} [{self.get_role_display()}] - {self.elo}"

    @property
    def rank(self):
        from .elo import get_rank
        return get_rank(self.elo)


class Fight(models.Model):
    """A ZvZ roaming fight."""

    title = models.CharField(max_length=200, blank=True, default="")
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Fight {self.id} - {self.date:%Y-%m-%d}"


class FightParticipant(models.Model):
    """A player's participation in a fight with their role."""

    fight = models.ForeignKey(
        Fight, on_delete=models.CASCADE, related_name="participants"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="participations"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    kill_fame = models.PositiveIntegerField(default=0)
    deaths = models.PositiveIntegerField(default=0)
    healing_done = models.PositiveIntegerField(default=0)
    damage_done = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)

    # Elo snapshot at the time of the fight
    elo_before = models.IntegerField(default=0)
    elo_after = models.IntegerField(default=0)

    # Auto-calculated performance score (0-10)
    performance_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=5.0
    )

    class Meta:
        unique_together = ("fight", "player")
        ordering = ["role"]

    def __str__(self):
        return f"{self.player.name} in Fight {self.fight_id}"
