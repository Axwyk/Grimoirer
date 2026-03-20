from django.contrib import admin
from .models import Player, PlayerElo, Fight, FightParticipant


class PlayerEloInline(admin.TabularInline):
    model = PlayerElo
    extra = 0


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["name", "guild", "created_at"]
    search_fields = ["name", "guild"]
    inlines = [PlayerEloInline]


class FightParticipantInline(admin.TabularInline):
    model = FightParticipant
    extra = 0
    readonly_fields = ["elo_before", "elo_after", "performance_score"]


@admin.register(Fight)
class FightAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "date"]
    list_filter = ["date"]
    inlines = [FightParticipantInline]


@admin.register(PlayerElo)
class PlayerEloAdmin(admin.ModelAdmin):
    list_display = ["player", "role", "elo", "total_games", "peak_elo"]
    list_filter = ["role"]
    search_fields = ["player__name"]
