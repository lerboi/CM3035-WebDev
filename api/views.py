"""
API Views for the Netflix API.

This module contains all REST API endpoint views for querying and managing
Netflix title data.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Min, Max, Q
from django.db.models.functions import ExtractYear
from django.shortcuts import render
from datetime import datetime, timedelta
from .models import NetflixTitle
from .serializers import NetflixTitleSerializer


# =============================================================================
# HOME PAGE
# =============================================================================

def home(request):
    """
    Main landing page with API documentation and navigation.
    
    GET /
    
    Displays:
    - Welcome message
    - All 6 API endpoints with descriptions
    - Example usage
    - Quick start guide
    """
    return render(request, 'api/home.html')


# ============================================================================
# ENDPOINT 1: List Titles with Optional Filters
# ============================================================================

@api_view(['GET'])
def title_list(request):
    """
    GET /api/titles/
    
    List all Netflix titles with optional filtering.
    
    Query Parameters:
    - type: Filter by content type ('Movie' or 'TV Show')
    - rating: Filter by content rating (e.g., 'TV-MA', 'PG-13')
    - year: Filter by release year
    
    Example:
    - /api/titles/
    - /api/titles/?type=Movie
    - /api/titles/?rating=TV-MA
    - /api/titles/?year=2020
    - /api/titles/?type=Movie&year=2020
    """
    queryset = NetflixTitle.objects.all()
    
    # Apply filters based on query parameters
    content_type = request.GET.get('type')
    rating = request.GET.get('rating')
    year = request.GET.get('year')
    
    if content_type:
        queryset = queryset.filter(type=content_type)
    
    if rating:
        queryset = queryset.filter(rating=rating)
    
    if year:
        try:
            year_int = int(year)
            queryset = queryset.filter(release_year=year_int)
        except ValueError:
            return Response(
                {'error': 'Year must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    return Response(serializer.data)


# ============================================================================
# ENDPOINT 2: Create New Title (POST)
# ============================================================================

@api_view(['POST'])
def title_create(request):
    """
    POST /api/titles/create/
    
    Create a new Netflix title.
    
    Required fields:
    - show_id: Unique identifier
    - type: 'Movie' or 'TV Show'
    - title: Title name
    - release_year: Year (1900-2030)
    - duration: Duration string
    - listed_in: Genres (comma-separated)
    - description: Description text
    
    Optional fields:
    - director, cast, country, date_added, rating
    
    Returns:
    - 201 Created: Title created successfully
    - 400 Bad Request: Validation errors
    """
    serializer = NetflixTitleSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# ENDPOINT 3: Statistics Dashboard
# ============================================================================

@api_view(['GET'])
def statistics(request):
    """
    GET /api/statistics/
    
    Comprehensive analytics dashboard with multiple aggregations.
    
    Returns:
    - total_count: Total number of titles
    - type_distribution: Count by type (Movie/TV Show)
    - rating_breakdown: Count by rating
    - content_by_year: Count of titles by release year
    - top_countries: Top 10 countries by content count
    - decade_analysis: Content distribution by decade
    - average_stats: Average release year, min/max years
    """
    # Basic counts
    total_count = NetflixTitle.objects.count()
    
    # Type distribution
    type_distribution = NetflixTitle.objects.values('type').annotate(
        count=Count('show_id')
    ).order_by('-count')
    
    # Rating breakdown
    rating_breakdown = NetflixTitle.objects.values('rating').annotate(
        count=Count('show_id')
    ).order_by('-count')
    
    # Content by year
    content_by_year = NetflixTitle.objects.values('release_year').annotate(
        count=Count('show_id')
    ).order_by('-release_year')
    
    # Top countries (parse comma-separated countries)
    # Note: This is a simplified version - for production, consider a separate Country model
    country_titles = NetflixTitle.objects.exclude(country__isnull=True).exclude(country='')
    country_counts = {}
    for title in country_titles:
        countries = [c.strip() for c in title.country.split(',')]
        for country in countries:
            country_counts[country] = country_counts.get(country, 0) + 1
    
    top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_countries_data = [{'country': c[0], 'count': c[1]} for c in top_countries]
    
    # Decade analysis
    decade_data = NetflixTitle.objects.annotate(
        decade=ExtractYear('release_year')
    ).values('release_year').annotate(
        count=Count('show_id')
    )
    
    # Group by decade
    decade_counts = {}
    for item in decade_data:
        decade = (item['release_year'] // 10) * 10
        decade_counts[decade] = decade_counts.get(decade, 0) + item['count']
    
    decade_analysis = [
        {'decade': f"{d}s", 'count': c} 
        for d, c in sorted(decade_counts.items(), reverse=True)
    ]
    
    # Average statistics
    avg_stats = NetflixTitle.objects.aggregate(
        avg_year=Avg('release_year'),
        min_year=Min('release_year'),
        max_year=Max('release_year')
    )
    
    return Response({
        'total_count': total_count,
        'type_distribution': list(type_distribution),
        'rating_breakdown': list(rating_breakdown),
        'content_by_year': list(content_by_year)[:20],  # Limit to 20 most recent years
        'top_countries': top_countries_data,
        'decade_analysis': decade_analysis,
        'average_stats': avg_stats
    })


# ============================================================================
# ENDPOINT 4: Advanced Search (Most Complex)
# ============================================================================

@api_view(['GET'])
def title_search(request):
    """
    GET /api/titles/search/
    
    Advanced multi-filter search with Q objects.
    
    Query Parameters:
    - type: Content type ('Movie' or 'TV Show')
    - rating: Content rating
    - country: Country name (partial match)
    - year_min: Minimum release year
    - year_max: Maximum release year
    - genre: Genre (searches in listed_in field)
    - director: Director name (partial match)
    - cast: Cast member name (partial match)
    - title: Title keyword (partial match)
    
    Example:
    - /api/titles/search/?genre=Action
    - /api/titles/search/?country=United%20States&year_min=2020
    - /api/titles/search/?type=Movie&rating=PG-13&genre=Drama
    """
    queryset = NetflixTitle.objects.all()
    
    # Build Q object for complex queries
    filters = Q()
    
    # Type filter
    content_type = request.GET.get('type')
    if content_type:
        filters &= Q(type=content_type)
    
    # Rating filter
    rating = request.GET.get('rating')
    if rating:
        filters &= Q(rating=rating)
    
    # Country filter (case-insensitive partial match)
    country = request.GET.get('country')
    if country:
        filters &= Q(country__icontains=country)
    
    # Year range filters
    year_min = request.GET.get('year_min')
    if year_min:
        try:
            filters &= Q(release_year__gte=int(year_min))
        except ValueError:
            return Response(
                {'error': 'year_min must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    year_max = request.GET.get('year_max')
    if year_max:
        try:
            filters &= Q(release_year__lte=int(year_max))
        except ValueError:
            return Response(
                {'error': 'year_max must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Genre filter (searches in listed_in field)
    genre = request.GET.get('genre')
    if genre:
        filters &= Q(listed_in__icontains=genre)
    
    # Director filter (case-insensitive partial match)
    director = request.GET.get('director')
    if director:
        filters &= Q(director__icontains=director)
    
    # Cast filter (case-insensitive partial match)
    cast_member = request.GET.get('cast')
    if cast_member:
        filters &= Q(cast__icontains=cast_member)
    
    # Title keyword filter (case-insensitive partial match)
    title_keyword = request.GET.get('title')
    if title_keyword:
        filters &= Q(title__icontains=title_keyword)
    
    # Apply all filters
    queryset = queryset.filter(filters)
    
    # Count results
    result_count = queryset.count()
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    
    return Response({
        'count': result_count,
        'results': serializer.data
    })


# ============================================================================
# ENDPOINT 5: Country-Specific Content
# ============================================================================

@api_view(['GET'])
def country_titles(request, country_name):
    """
    GET /api/country/<country_name>/
    
    Get all titles from a specific country with statistics.
    
    URL Parameter:
    - country_name: Name of the country
    
    Example:
    - /api/country/United States/
    - /api/country/India/
    
    Returns:
    - count: Total titles from this country
    - country: Country name
    - statistics: Type breakdown, average year
    - titles: List of titles
    """
    # Filter titles by country (case-insensitive partial match)
    queryset = NetflixTitle.objects.filter(country__icontains=country_name)
    
    if not queryset.exists():
        return Response(
            {'error': f'No titles found for country: {country_name}'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate statistics
    total_count = queryset.count()
    type_breakdown = queryset.values('type').annotate(count=Count('show_id'))
    avg_year = queryset.aggregate(avg_year=Avg('release_year'))
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    
    return Response({
        'count': total_count,
        'country': country_name,
        'statistics': {
            'type_breakdown': list(type_breakdown),
            'average_release_year': avg_year['avg_year']
        },
        'titles': serializer.data
    })


# ============================================================================
# ENDPOINT 6: Personalized Recommendations
# ============================================================================

@api_view(['GET'])
def recommendations(request):
    """
    GET /api/recommendations/
    
    Get personalized recommendations based on genre preference.
    
    Query Parameters:
    - genre: Required genre for recommendations
    - type: Optional content type filter ('Movie' or 'TV Show')
    - recent: Optional boolean to show only recent content (last 3 years)
    
    Example:
    - /api/recommendations/?genre=Action
    - /api/recommendations/?genre=Drama&type=Movie
    - /api/recommendations/?genre=Comedy&recent=true
    
    Returns:
    - Up to 20 recommendations matching the criteria
    """
    # Genre is required
    genre = request.GET.get('genre')
    if not genre:
        return Response(
            {'error': 'genre parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Start with genre filter
    queryset = NetflixTitle.objects.filter(listed_in__icontains=genre)
    
    # Optional type filter
    content_type = request.GET.get('type')
    if content_type:
        queryset = queryset.filter(type=content_type)
    
    # Optional recent content filter (last 3 years)
    recent = request.GET.get('recent')
    if recent and recent.lower() == 'true':
        current_year = datetime.now().year
        three_years_ago = current_year - 3
        queryset = queryset.filter(release_year__gte=three_years_ago)
    
    # Order by release year (most recent first) and limit to 20
    queryset = queryset.order_by('-release_year', '-date_added')[:20]
    
    if not queryset.exists():
        return Response(
            {'message': 'No recommendations found for the given criteria'},
            status=status.HTTP_200_OK
        )
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    
    return Response({
        'genre': genre,
        'count': len(serializer.data),
        'recommendations': serializer.data
    })