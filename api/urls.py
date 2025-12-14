"""
URL configuration for the Netflix API.

Maps URL patterns to view functions for all API endpoints.
"""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Endpoint 1: List titles with optional filters
    # GET /api/titles/?type=Movie&rating=TV-MA&year=2020
    path('titles/', views.title_list, name='title-list'),
    
    # Endpoint 2: Create new title (POST required)
    # POST /api/titles/create/
    path('titles/create/', views.title_create, name='title-create'),
    
    # Endpoint 3: Statistics dashboard
    # GET /api/statistics/
    path('statistics/', views.statistics, name='statistics'),
    
    # Endpoint 4: Advanced search (most complex)
    # GET /api/titles/search/?genre=Action&country=United%20States
    path('titles/search/', views.title_search, name='title-search'),
    
    # Endpoint 5: Country-specific content
    # GET /api/country/United%20States/
    path('country/<str:country_name>/', views.country_titles, name='country-titles'),
    
    # Endpoint 6: Personalized recommendations
    # GET /api/recommendations/?genre=Drama&type=Movie&recent=true
    path('recommendations/', views.recommendations, name='recommendations'),
]