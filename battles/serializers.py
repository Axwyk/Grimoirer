from rest_framework import serializers

from battles.models import Battle, PlayerBattleStats, ALBION_RENDER_URL, get_subrole_from_weapon
from events.models import Event


class PlayerBattleStatsSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name')
    player_guild = serializers.CharField(source='player.guild_name')
    weapon_icon = serializers.SerializerMethodField()
    sub_role = serializers.SerializerMethodField()

    class Meta:
        model = PlayerBattleStats
        fields = [
            'id', 'player', 'player_name', 'player_guild',
            'damage_done', 'healing_done', 'kills', 'deaths', 'assists',
            'kill_fame', 'average_item_power', 'main_weapon', 'role', 'sub_role', 'weapon_icon',
            'raw_score', 'normalized_score',
            'elo_before', 'elo_after', 'elo_change',
        ]

    def get_weapon_icon(self, obj):
        if obj.main_weapon:
            return ALBION_RENDER_URL.format(item_id=obj.main_weapon)
        return None

    def get_sub_role(self, obj):
        return get_subrole_from_weapon(obj.main_weapon)


class KillEventSerializer(serializers.ModelSerializer):
    killer_name = serializers.CharField(source='killer.name')
    victim_name = serializers.CharField(source='victim.name')
    killer_id = serializers.IntegerField(source='killer.pk')
    victim_id = serializers.IntegerField(source='victim.pk')

    class Meta:
        model = Event
        fields = [
            'id', 'event_id', 'timestamp',
            'killer_id', 'killer_name',
            'victim_id', 'victim_name',
            'total_kill_fame',
        ]


class BattleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Battle
        fields = [
            'id', 'zone', 'start_time', 'end_time',
            'total_players', 'total_kills', 'total_guilds',
            'is_valid', 'processed', 'elo_updated',
        ]


class BattleDetailSerializer(serializers.ModelSerializer):
    player_stats = PlayerBattleStatsSerializer(many=True, read_only=True)
    kill_feed = serializers.SerializerMethodField()

    class Meta:
        model = Battle
        fields = [
            'id', 'zone', 'start_time', 'end_time',
            'total_players', 'total_kills', 'total_guilds',
            'is_valid', 'processed', 'elo_updated',
            'player_stats', 'kill_feed',
        ]

    def get_kill_feed(self, obj):
        events = (
            obj.events
            .select_related('killer', 'victim')
            .order_by('timestamp')
        )
        return KillEventSerializer(events, many=True).data
