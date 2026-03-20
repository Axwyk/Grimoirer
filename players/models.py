from django.db import models


class Player(models.Model):
    albion_id = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100, db_index=True)
    guild_name = models.CharField(max_length=100, blank=True, default='')
    guild_id = models.CharField(max_length=64, blank=True, default='')
    alliance_name = models.CharField(max_length=100, blank=True, default='')
    alliance_id = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        guild = f' [{self.guild_name}]' if self.guild_name else ''
        return f'{self.name}{guild}'
