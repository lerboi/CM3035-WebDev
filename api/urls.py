from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('titles/', views.title_list, name='title-list'),
    path('titles/create/', views.title_create, name='title-create'),
    path('statistics/', views.statistics, name='statistics'),
    path('titles/search/', views.title_search, name='title-search'),
    path('country/<str:country_name>/', views.country_titles, name='country-titles'),
    path('recommendations/', views.recommendations, name='recommendations'),
]