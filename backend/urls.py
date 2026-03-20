"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ranking import views as ranking_views


@api_view(['GET'])
def api_root(request):
    return Response({
        'endpoints': {
            'ranking': request.build_absolute_uri('/api/ranking/'),
            'battles': request.build_absolute_uri('/api/battles/'),
            'players': request.build_absolute_uri('/api/players/'),
            'stats': request.build_absolute_uri('/api/stats/'),
        }
    })


urlpatterns = [
    path('', api_root),
    path('admin/', admin.site.urls),
    path('api/players/', include('players.urls')),
    path('api/battles/', include('battles.urls')),
    path('api/ranking/', include('ranking.urls')),
    path('api/players/<int:player_id>/stats/', ranking_views.player_battle_history),
    path('api/stats/', ranking_views.ranking_overview),
]
