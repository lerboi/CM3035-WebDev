from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Min, Max, Q
from django.shortcuts import render
from datetime import datetime
from .models import NetflixTitle
from .serializers import NetflixTitleSerializer


# Renders the main landing page with API documentation
def home(request):
    return render(request, 'api/home.html')


# Returns all titles, optionally filtered by type, rating, or year
@api_view(['GET'])
def title_list(request):
    queryset = NetflixTitle.objects.all()
    
    content_type = request.GET.get('type')
    rating = request.GET.get('rating')
    year = request.GET.get('year')
    
    if content_type:
        queryset = queryset.filter(type=content_type)
    
    if rating:
        queryset = queryset.filter(rating=rating)
    
    if year:
        try:
            queryset = queryset.filter(release_year=int(year))
        except ValueError:
            return Response({'error': 'Year must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    return Response(serializer.data)


# Creates a new Netflix title from JSON data
@api_view(['POST'])
def title_create(request):
    serializer = NetflixTitleSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Returns statistics about the Netflix catalog (counts, averages, top countries)
@api_view(['GET'])
def statistics(request):
    total_count = NetflixTitle.objects.count()
    
    type_distribution = NetflixTitle.objects.values('type').annotate(count=Count('show_id')).order_by('-count')
    
    rating_breakdown = NetflixTitle.objects.values('rating').annotate(count=Count('show_id')).order_by('-count')
    
    content_by_year = NetflixTitle.objects.values('release_year').annotate(count=Count('show_id')).order_by('-release_year')
    
    # Count titles per country
    country_titles = NetflixTitle.objects.exclude(country__isnull=True).exclude(country='')
    country_counts = {}
    for title in country_titles:
        for country in [c.strip() for c in title.country.split(',')]:
            country_counts[country] = country_counts.get(country, 0) + 1
    
    top_countries = [{'country': c, 'count': n} for c, n in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    # Group by decade
    decade_data = NetflixTitle.objects.values('release_year').annotate(count=Count('show_id'))
    decade_counts = {}
    for item in decade_data:
        decade = (item['release_year'] // 10) * 10
        decade_counts[decade] = decade_counts.get(decade, 0) + item['count']
    decade_analysis = [{'decade': f"{d}s", 'count': c} for d, c in sorted(decade_counts.items(), reverse=True)]
    
    avg_stats = NetflixTitle.objects.aggregate(avg_year=Avg('release_year'), min_year=Min('release_year'), max_year=Max('release_year'))
    
    return Response({
        'total_count': total_count,
        'type_distribution': list(type_distribution),
        'rating_breakdown': list(rating_breakdown),
        'content_by_year': list(content_by_year)[:20],
        'top_countries': top_countries,
        'decade_analysis': decade_analysis,
        'average_stats': avg_stats
    })


# Advanced search with multiple optional filters (type, rating, country, year range, genre, director, cast, title)
@api_view(['GET'])
def title_search(request):
    queryset = NetflixTitle.objects.all()
    filters = Q()
    
    content_type = request.GET.get('type')
    if content_type:
        filters &= Q(type=content_type)
    
    rating = request.GET.get('rating')
    if rating:
        filters &= Q(rating=rating)
    
    country = request.GET.get('country')
    if country:
        filters &= Q(country__icontains=country)
    
    year_min = request.GET.get('year_min')
    if year_min:
        try:
            filters &= Q(release_year__gte=int(year_min))
        except ValueError:
            return Response({'error': 'year_min must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)
    
    year_max = request.GET.get('year_max')
    if year_max:
        try:
            filters &= Q(release_year__lte=int(year_max))
        except ValueError:
            return Response({'error': 'year_max must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)
    
    genre = request.GET.get('genre')
    if genre:
        filters &= Q(listed_in__icontains=genre)
    
    director = request.GET.get('director')
    if director:
        filters &= Q(director__icontains=director)
    
    cast_member = request.GET.get('cast')
    if cast_member:
        filters &= Q(cast__icontains=cast_member)
    
    title_keyword = request.GET.get('title')
    if title_keyword:
        filters &= Q(title__icontains=title_keyword)
    
    queryset = queryset.filter(filters)
    serializer = NetflixTitleSerializer(queryset, many=True)
    
    return Response({'count': queryset.count(), 'results': serializer.data})


# Returns all titles from a specific country with statistics
@api_view(['GET'])
def country_titles(request, country_name):
    queryset = NetflixTitle.objects.filter(country__icontains=country_name)
    
    if not queryset.exists():
        return Response({'error': f'No titles found for country: {country_name}'}, status=status.HTTP_404_NOT_FOUND)
    
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


# Returns up to 20 recommended titles based on genre, type, and recency
@api_view(['GET'])
def recommendations(request):
    genre = request.GET.get('genre')
    if not genre:
        return Response({'error': 'genre parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    queryset = NetflixTitle.objects.filter(listed_in__icontains=genre)
    
    content_type = request.GET.get('type')
    if content_type:
        queryset = queryset.filter(type=content_type)
    
    recent = request.GET.get('recent')
    if recent and recent.lower() == 'true':
        three_years_ago = datetime.now().year - 3
        queryset = queryset.filter(release_year__gte=three_years_ago)
    
    queryset = queryset.order_by('-release_year', '-date_added')[:20]
    
    if not queryset.exists():
        return Response({'message': 'No recommendations found for the given criteria'}, status=status.HTTP_200_OK)
    
    serializer = NetflixTitleSerializer(queryset, many=True)
    
    return Response({
        'genre': genre,
        'count': len(serializer.data),
        'recommendations': serializer.data
    })