from django.urls import path, include
from rest_framework.routers import DefaultRouter

from battles import views

router = DefaultRouter()
router.register(r'', views.BattleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
