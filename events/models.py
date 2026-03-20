from django.db import models


class Event(models.Model):
    event_id = models.BigIntegerField(unique=True, db_index=True)
    battle_id_api = models.BigIntegerField(db_index=True, null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    zone = models.CharField(max_length=200, db_index=True)

    killer = models.ForeignKey(
        'players.Player', on_delete=models.CASCADE, related_name='kills_as_killer'
    )
    victim = models.ForeignKey(
        'players.Player', on_delete=models.CASCADE, related_name='deaths_as_victim'
    )
    total_kill_fame = models.BigIntegerField(default=0)
    number_of_participants = models.IntegerField(default=0)

    raw_data = models.JSONField(default=dict)

    battle = models.ForeignKey(
        'battles.Battle', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='events'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['zone', 'timestamp']),
        ]

    def __str__(self):
        return f'Event {self.event_id}: {self.killer} → {self.victim}'


class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    damage_done = models.FloatField(default=0)
    healing_done = models.FloatField(default=0)

    class Meta:
        unique_together = ('event', 'player')

    def __str__(self):
        return f'{self.player} in Event {self.event.event_id}'
