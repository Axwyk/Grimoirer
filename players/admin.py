from django.contrib import admin

from players.models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'guild_name', 'alliance_name', 'albion_id', 'created_at']
    search_fields = ['name', 'guild_name', 'albion_id']
    list_filter = ['guild_name']
    readonly_fields = ['albion_id', 'created_at', 'updated_at']
