from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import NetflixTitle
from api.serializers import NetflixTitleSerializer
from datetime import date

class NetflixTitleModelTest(TestCase):
    def setUp(self):
        self.movie = NetflixTitle.objects.create(
            show_id='s1', type='Movie', title='Test Movie', director='Test Director',
            cast='Actor One, Actor Two, Actor Three', country='United States',
            date_added=date(2021, 1, 15), release_year=2020, rating='PG-13',
            duration='120 min', listed_in='Action, Drama, Thriller',
            description='A test movie description.'
        )
        self.tv_show = NetflixTitle.objects.create(
            show_id='s2', type='TV Show', title='Test TV Show', director=None,
            cast='Actor A, Actor B', country='United Kingdom',
            date_added=date(2020, 6, 1), release_year=2019, rating='TV-MA',
            duration='3 Seasons', listed_in='Drama, International TV Shows',
            description='A test TV show description.'
        )

    # returns correct format for movie
    def test_model_str_representation(self):
        self.assertEqual(str(self.movie), 'Test Movie (2020) - Movie')

    # returns correct format for TV show
    def test_model_str_representation_tv_show(self):
        self.assertEqual(str(self.tv_show), 'Test TV Show (2019) - TV Show')

    # splits comma-separated genres
    def test_get_genres_method(self):
        genres = self.movie.get_genres()
        self.assertEqual(len(genres), 3)
        self.assertIn('Action', genres)

    # splits comma-separated cast
    def test_get_cast_list_method(self):
        cast = self.movie.get_cast_list()
        self.assertEqual(len(cast), 3)
        self.assertIn('Actor One', cast)

    # returns empty list when cast is None
    def test_get_cast_list_empty(self):
        self.movie.cast = None
        self.movie.save()
        self.assertEqual(self.movie.get_cast_list(), [])

    # Textracts minutes from movie duration
    def test_get_duration_minutes_movie(self):
        self.assertEqual(self.movie.get_duration_minutes(), 120)

    # returns None for TV shows
    def test_get_duration_minutes_tv_show(self):
        self.assertIsNone(self.tv_show.get_duration_minutes())

    # extracts seasons from TV show
    def test_get_duration_seasons_tv_show(self):
        self.assertEqual(self.tv_show.get_duration_seasons(), 3)

    # returns None for movies
    def test_get_duration_seasons_movie(self):
        self.assertIsNone(self.movie.get_duration_seasons())

    # is by date_added descending
    def test_model_ordering(self):
        titles = NetflixTitle.objects.all()
        self.assertEqual(titles[0].show_id, 's1')


# Tests for the NetflixTitleSerializer
class NetflixTitleSerializerTest(TestCase):
    # Test serializer accepts valid data
    def test_serializer_valid_data(self):
        data = {'show_id': 's100', 'type': 'Movie', 'title': 'Valid Movie',
                'release_year': 2020, 'duration': '90 min', 'listed_in': 'Comedy',
                'description': 'A valid description.'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    # rejects invalid type
    def test_serializer_invalid_type(self):
        data = {'show_id': 's101', 'type': 'Invalid', 'title': 'Test',
                'release_year': 2020, 'duration': '90 min', 'listed_in': 'Comedy',
                'description': 'Test.'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)

    # rejects year below 1900
    def test_serializer_invalid_year_low(self):
        data = {'show_id': 's102', 'type': 'Movie', 'title': 'Old',
                'release_year': 1800, 'duration': '90 min', 'listed_in': 'Drama',
                'description': 'Too old.'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    # rejects year above 2030
    def test_serializer_invalid_year_high(self):
        data = {'show_id': 's103', 'type': 'Movie', 'title': 'Future',
                'release_year': 2050, 'duration': '90 min', 'listed_in': 'Sci-Fi',
                'description': 'Too far.'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    # Test created_at and updated_at are read-only
    def test_serializer_read_only_fields(self):
        data = {'show_id': 's104', 'type': 'Movie', 'title': 'Test',
                'release_year': 2020, 'duration': '90 min', 'listed_in': 'Action',
                'description': 'Test.', 'created_at': '2020-01-01T00:00:00Z'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    # rejects missing required fields
    def test_serializer_missing_required_field(self):
        data = {'show_id': 's105', 'type': 'Movie'}
        serializer = NetflixTitleSerializer(data=data)
        self.assertFalse(serializer.is_valid())


# Tests for GET /api/titles/ endpoint
class TitleListEndpointTest(APITestCase):
    def setUp(self):
        NetflixTitle.objects.create(show_id='s1', type='Movie', title='Movie One',
            release_year=2020, rating='PG-13', duration='90 min',
            listed_in='Action', description='Action movie.')
        NetflixTitle.objects.create(show_id='s2', type='TV Show', title='TV Show One',
            release_year=2019, rating='TV-MA', duration='2 Seasons',
            listed_in='Drama', description='Drama show.')
        NetflixTitle.objects.create(show_id='s3', type='Movie', title='Movie Two',
            release_year=2020, rating='R', duration='120 min',
            listed_in='Horror', description='Horror movie.')

    # Test retrieving all titles
    def test_list_all_titles(self):
        response = self.client.get(reverse('api:title-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    # Test filtering by type=Movie
    def test_filter_by_type_movie(self):
        response = self.client.get(reverse('api:title-list'), {'type': 'Movie'})
        self.assertEqual(len(response.data), 2)

    # Test filtering by type=TV Show
    def test_filter_by_type_tv_show(self):
        response = self.client.get(reverse('api:title-list'), {'type': 'TV Show'})
        self.assertEqual(len(response.data), 1)

    # Test filtering by rating
    def test_filter_by_rating(self):
        response = self.client.get(reverse('api:title-list'), {'rating': 'PG-13'})
        self.assertEqual(len(response.data), 1)

    # Test filtering by year
    def test_filter_by_year(self):
        response = self.client.get(reverse('api:title-list'), {'year': '2020'})
        self.assertEqual(len(response.data), 2)

    # Test invalid year returns error
    def test_filter_invalid_year(self):
        response = self.client.get(reverse('api:title-list'), {'year': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Tests for POST /api/titles/create/ endpoint.
class TitleCreateEndpointTest(APITestCase):
    # Test successful title creation
    def test_create_title_success(self):
        data = {'show_id': 's999', 'type': 'Movie', 'title': 'New Movie',
                'release_year': 2021, 'duration': '100 min', 'listed_in': 'Comedy',
                'description': 'A new comedy movie.'}
        response = self.client.post(reverse('api:title-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Test invalid data returns 400
    def test_create_title_invalid_data(self):
        data = {'show_id': 's998', 'type': 'Invalid', 'title': 'Bad',
                'release_year': 2021, 'duration': '100 min', 'listed_in': 'Action',
                'description': 'Description.'}
        response = self.client.post(reverse('api:title-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test duplicate show_id is rejected
    def test_create_title_duplicate_show_id(self):
        NetflixTitle.objects.create(show_id='s500', type='Movie', title='Existing',
            release_year=2020, duration='90 min', listed_in='Drama', description='Existing.')
        data = {'show_id': 's500', 'type': 'Movie', 'title': 'Duplicate',
                'release_year': 2021, 'duration': '100 min', 'listed_in': 'Action',
                'description': 'Description.'}
        response = self.client.post(reverse('api:title-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test missing required fields returns error
    def test_create_title_missing_required_fields(self):
        data = {'show_id': 's997', 'type': 'Movie'}
        response = self.client.post(reverse('api:title-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Tests for GET /api/statistics/ endpoint
class StatisticsEndpointTest(APITestCase):
    def setUp(self):
        NetflixTitle.objects.create(show_id='s1', type='Movie', title='Movie 1',
            release_year=2020, rating='PG-13', duration='90 min',
            listed_in='Action', description='Test.', country='United States')
        NetflixTitle.objects.create(show_id='s2', type='Movie', title='Movie 2',
            release_year=2019, rating='R', duration='100 min',
            listed_in='Drama', description='Test.', country='United States')
        NetflixTitle.objects.create(show_id='s3', type='TV Show', title='Show 1',
            release_year=2020, rating='TV-MA', duration='2 Seasons',
            listed_in='Drama', description='Test.', country='India')

    # Test statistics returns expected keys
    def test_statistics_returns_data(self):
        response = self.client.get(reverse('api:statistics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_count', response.data)
        self.assertIn('type_distribution', response.data)

    # Test total count is correct
    def test_statistics_total_count(self):
        response = self.client.get(reverse('api:statistics'))
        self.assertEqual(response.data['total_count'], 3)

    # Test type distribution is correct
    def test_statistics_type_distribution(self):
        response = self.client.get(reverse('api:statistics'))
        type_dist = {item['type']: item['count'] for item in response.data['type_distribution']}
        self.assertEqual(type_dist['Movie'], 2)


# Tests for GET /api/titles/search/ endpoint
class TitleSearchEndpointTest(APITestCase):
    def setUp(self):
        NetflixTitle.objects.create(show_id='s1', type='Movie', title='Action Movie',
            director='John Director', cast='Actor One', release_year=2020,
            rating='PG-13', duration='90 min', listed_in='Action, Adventure',
            description='Action film.', country='United States')
        NetflixTitle.objects.create(show_id='s2', type='TV Show', title='Drama Series',
            director='Jane Director', cast='Actor Two', release_year=2018,
            rating='TV-MA', duration='3 Seasons', listed_in='Drama, International',
            description='Drama show.', country='United Kingdom')
        NetflixTitle.objects.create(show_id='s3', type='Movie', title='Comedy Film',
            director='John Director', cast='Actor Three', release_year=2021,
            rating='PG', duration='85 min', listed_in='Comedy',
            description='Funny movie.', country='United States')

    # Test searching by genre
    def test_search_by_genre(self):
        response = self.client.get(reverse('api:title-search'), {'genre': 'Action'})
        self.assertEqual(response.data['count'], 1)

    # Test searching by director
    def test_search_by_director(self):
        response = self.client.get(reverse('api:title-search'), {'director': 'John'})
        self.assertEqual(response.data['count'], 2)

    # Test searching by year range
    def test_search_by_year_range(self):
        response = self.client.get(reverse('api:title-search'), {'year_min': '2019', 'year_max': '2020'})
        self.assertEqual(response.data['count'], 1)

    # Test searching by country
    def test_search_by_country(self):
        response = self.client.get(reverse('api:title-search'), {'country': 'United States'})
        self.assertEqual(response.data['count'], 2)

    # Test combining multiple filters
    def test_search_multiple_filters(self):
        response = self.client.get(reverse('api:title-search'), 
            {'type': 'Movie', 'country': 'United States', 'year_min': '2020'})
        self.assertEqual(response.data['count'], 2)

    # Test search with no results
    def test_search_no_results(self):
        response = self.client.get(reverse('api:title-search'), {'genre': 'NonexistentGenre'})
        self.assertEqual(response.data['count'], 0)


# Tests for GET /api/country/<country_name>/ endpoint
class CountryTitlesEndpointTest(APITestCase):
    def setUp(self):
        NetflixTitle.objects.create(show_id='s1', type='Movie', title='US Movie',
            release_year=2020, duration='90 min', listed_in='Action',
            description='Test.', country='United States')
        NetflixTitle.objects.create(show_id='s2', type='TV Show', title='US Show',
            release_year=2019, duration='2 Seasons', listed_in='Drama',
            description='Test.', country='United States')
        NetflixTitle.objects.create(show_id='s3', type='Movie', title='UK Movie',
            release_year=2020, duration='100 min', listed_in='Comedy',
            description='Test.', country='United Kingdom')

    # Test retrieving titles for a valid country
    def test_country_titles_success(self):
        response = self.client.get(reverse('api:country-titles', kwargs={'country_name': 'United States'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    # Test country endpoint returns statistics
    def test_country_titles_statistics(self):
        response = self.client.get(reverse('api:country-titles', kwargs={'country_name': 'United States'}))
        self.assertIn('statistics', response.data)

    # Test 404 for non-existent country
    def test_country_titles_not_found(self):
        response = self.client.get(reverse('api:country-titles', kwargs={'country_name': 'Nonexistent'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Tests for GET /api/recommendations/ endpoint
class RecommendationsEndpointTest(APITestCase):
    def setUp(self):
        NetflixTitle.objects.create(show_id='s1', type='Movie', title='Action Movie 1',
            release_year=2023, duration='90 min', listed_in='Action, Thriller',
            description='Action film.')
        NetflixTitle.objects.create(show_id='s2', type='Movie', title='Action Movie 2',
            release_year=2020, duration='100 min', listed_in='Action',
            description='Another action.')
        NetflixTitle.objects.create(show_id='s3', type='TV Show', title='Drama Show',
            release_year=2021, duration='2 Seasons', listed_in='Drama',
            description='Drama series.')

    # Test genre parameter is required
    def test_recommendations_requires_genre(self):
        response = self.client.get(reverse('api:recommendations'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test recommendations with genre
    def test_recommendations_with_genre(self):
        response = self.client.get(reverse('api:recommendations'), {'genre': 'Action'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    # Test recommendations with type filter
    def test_recommendations_with_type_filter(self):
        response = self.client.get(reverse('api:recommendations'), {'genre': 'Action', 'type': 'Movie'})
        self.assertEqual(response.data['count'], 2)

    # Test recommendations with no matches
    def test_recommendations_no_matches(self):
        response = self.client.get(reverse('api:recommendations'), {'genre': 'SciFi'})
        self.assertIn('message', response.data)


# Tests for the home page
class HomePageTest(APITestCase):
    # Test home page loads successfully
    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Test home page contains required system info
    def test_home_page_contains_required_info(self):
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        self.assertIn('Python', content)
        self.assertIn('Django', content)