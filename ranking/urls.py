from django.urls import path

from ranking import views

urlpatterns = [
    path('', views.ranking_list, name='ranking-list'),
    path('overview/', views.ranking_overview, name='ranking-overview'),
]
