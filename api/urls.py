from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('titles/', views.title_list, name='title-list'), # GET: List all titles with filters
    path('titles/create/', views.title_create, name='title-create'), # POST: Create new title
    path('statistics/', views.statistics, name='statistics'), # GET: Catalog statistics
    path('titles/search/', views.title_search, name='title-search'), # GET: Advanced search
    path('country/<str:country_name>/', views.country_titles, name='country-titles'), # GET: Titles by country
    path('recommendations/', views.recommendations, name='recommendations'), # GET: Genre recommendations
]