from rest_framework import serializers

from ranking.models import Rating
from battles.models import PlayerBattleStats, ALBION_RENDER_URL


class RatingSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name')
    player_guild = serializers.CharField(source='player.guild_name')
    player_alliance = serializers.CharField(source='player.alliance_name')
    rank_name = serializers.SerializerMethodField()
    rank_color = serializers.SerializerMethodField()
    main_role = serializers.SerializerMethodField()
    main_weapon = serializers.SerializerMethodField()
    weapon_icon = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            'id', 'player', 'player_name', 'player_guild', 'player_alliance',
            'elo', 'peak_elo', 'total_battles',
            'rank_name', 'rank_color',
            'main_role', 'main_weapon', 'weapon_icon',
        ]

    def get_rank_name(self, obj):
        return obj.rank_tier['name']

    def get_rank_color(self, obj):
        return obj.rank_tier['color']

    def get_main_role(self, obj):
        """Rol más frecuente del jugador en sus batallas."""
        from django.db.models import Count
        top = (
            PlayerBattleStats.objects
            .filter(player=obj.player)
            .values('role')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        return top['role'] if top else 'DPS'

    def get_main_weapon(self, obj):
        """Arma más usada por el jugador."""
        from django.db.models import Count
        top = (
            PlayerBattleStats.objects
            .filter(player=obj.player)
            .exclude(main_weapon='')
            .values('main_weapon')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        return top['main_weapon'] if top else ''

    def get_weapon_icon(self, obj):
        weapon = self.get_main_weapon(obj)
        if weapon:
            return ALBION_RENDER_URL.format(item_id=weapon)
        return None
