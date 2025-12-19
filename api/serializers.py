from rest_framework import serializers
from .models import NetflixTitle

# Converts NetflixTitle objects to/from JSON.
class NetflixTitleSerializer(serializers.ModelSerializer):    
    class Meta:
        model = NetflixTitle
        fields = [
            'show_id', 'type', 'title', 'director', 'cast', 'country',
            'date_added', 'release_year', 'rating', 'duration',
            'listed_in', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    # Checks that release year is between 1900 and 2030
    def validate_release_year(self, value):
        if value < 1900 or value > 2030:
            raise serializers.ValidationError("Release year must be between 1900 and 2030.")
        return value
    
    # Checks that type is either 'Movie' or 'TV Show'
    def validate_type(self, value):
        if value not in ['Movie', 'TV Show']:
            raise serializers.ValidationError("Type must be either 'Movie' or 'TV Show'.")
        return value