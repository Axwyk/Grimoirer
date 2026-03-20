from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"players", views.PlayerViewSet)
router.register(r"fights", views.FightViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("leaderboard/<str:role>/", views.leaderboard, name="leaderboard"),
    path(
        "players/<int:player_id>/history/",
        views.player_history,
        name="player-history",
    ),
    path("stats/", views.stats_overview, name="stats-overview"),
]
