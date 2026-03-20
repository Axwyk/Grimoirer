from rest_framework import serializers

from players.models import Player


class PlayerSerializer(serializers.ModelSerializer):
    elo = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'albion_id', 'name', 'guild_name', 'alliance_name',
            'elo', 'rank', 'created_at',
        ]

    def get_elo(self, obj):
        if hasattr(obj, 'rating'):
            return obj.rating.elo
        return None

    def get_rank(self, obj):
        if hasattr(obj, 'rating'):
            tier = obj.rating.rank_tier
            return {'name': tier['name'], 'color': tier['color']}
        return None


class PlayerDetailSerializer(PlayerSerializer):
    total_battles = serializers.SerializerMethodField()
    peak_elo = serializers.SerializerMethodField()

    class Meta(PlayerSerializer.Meta):
        fields = PlayerSerializer.Meta.fields + [
            'guild_id', 'alliance_id', 'total_battles', 'peak_elo', 'updated_at',
        ]

    def get_total_battles(self, obj):
        if hasattr(obj, 'rating'):
            return obj.rating.total_battles
        return 0

    def get_peak_elo(self, obj):
        if hasattr(obj, 'rating'):
            return obj.rating.peak_elo
        return None
