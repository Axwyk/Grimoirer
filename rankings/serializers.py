from rest_framework import serializers
from .models import Player, PlayerElo, Fight, FightParticipant
from .elo import get_rank


class PlayerEloSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    player_name = serializers.CharField(source="player.name", read_only=True)
    player_guild = serializers.CharField(source="player.guild", read_only=True)
    rank_name = serializers.SerializerMethodField()
    rank_color = serializers.SerializerMethodField()

    class Meta:
        model = PlayerElo
        fields = [
            "id",
            "player",
            "player_name",
            "player_guild",
            "role",
            "role_display",
            "elo",
            "total_games",
            "peak_elo",
            "rank_name",
            "rank_color",
        ]

    def get_rank_name(self, obj):
        return get_rank(obj.elo)["name"]

    def get_rank_color(self, obj):
        return get_rank(obj.elo)["color"]


class PlayerSerializer(serializers.ModelSerializer):
    elos = PlayerEloSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = ["id", "name", "guild", "created_at", "elos"]


class FightParticipantSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = FightParticipant
        fields = [
            "id",
            "player",
            "player_name",
            "role",
            "role_display",
            "kill_fame",
            "deaths",
            "healing_done",
            "damage_done",
            "assists",
            "performance_score",
            "elo_before",
            "elo_after",
        ]


class FightSerializer(serializers.ModelSerializer):
    participants = FightParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Fight
        fields = [
            "id",
            "title",
            "date",
            "created_at",
            "notes",
            "participants",
        ]


class FightCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a fight with participants."""

    participants = FightParticipantSerializer(many=True)

    class Meta:
        model = Fight
        fields = ["id", "title", "date", "notes", "participants"]

    def create(self, validated_data):
        from .services import process_fight

        participants_data = validated_data.pop("participants")
        fight = Fight.objects.create(**validated_data)
        process_fight(fight, participants_data)
        return fight

        participants_data = validated_data.pop("participants")
        fight = Fight.objects.create(**validated_data)
        process_fight(fight, participants_data)
        return fight
