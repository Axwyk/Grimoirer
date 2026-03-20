from django.contrib import admin

from battles.models import Battle, PlayerBattleStats


class PlayerBattleStatsInline(admin.TabularInline):
    model = PlayerBattleStats
    extra = 0
    readonly_fields = [
        'player', 'damage_done', 'healing_done', 'kills', 'deaths',
        'assists', 'kill_fame', 'raw_score', 'normalized_score',
        'elo_before', 'elo_after', 'elo_change',
    ]


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'zone', 'start_time', 'total_players', 'total_kills',
        'total_guilds', 'is_valid', 'processed', 'elo_updated',
    ]
    list_filter = ['is_valid', 'processed', 'elo_updated']
    search_fields = ['zone']
    inlines = [PlayerBattleStatsInline]
