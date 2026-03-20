from django.contrib import admin

from ranking.models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['player', 'elo', 'peak_elo', 'total_battles', 'updated_at']
    search_fields = ['player__name', 'player__guild_name']
    readonly_fields = ['player', 'elo', 'peak_elo', 'total_battles']
    ordering = ['-elo']
