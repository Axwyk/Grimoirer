from rest_framework import viewsets

from battles.models import Battle
from battles.serializers import BattleListSerializer, BattleDetailSerializer


class BattleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Battle.objects.filter(is_valid=True).order_by('-start_time')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BattleDetailSerializer
        return BattleListSerializer
