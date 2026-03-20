from django.conf import settings as django_settings
from rest_framework import viewsets, filters

from players.models import Player
from players.serializers import PlayerSerializer, PlayerDetailSerializer


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'guild_name', 'alliance_name']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        qs = Player.objects.select_related('rating').all()
        tracked = getattr(django_settings, 'TRACKED_GUILD', None)
        if tracked:
            qs = qs.filter(guild_name=tracked)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlayerDetailSerializer
        return PlayerSerializer
