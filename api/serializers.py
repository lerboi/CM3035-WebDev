"""
Serializers for the Netflix API.

This module contains serializers for converting NetflixTitle model instances
to/from JSON format for the REST API.
"""

from rest_framework import serializers
from .models import NetflixTitle


class NetflixTitleSerializer(serializers.ModelSerializer):
    """
    Serializer for NetflixTitle model.
    
    Converts NetflixTitle instances to JSON and validates incoming data
    for POST requests.
    
    All fields from the model are included in the serialization.
    """
    
    class Meta:
        model = NetflixTitle
        fields = [
            'show_id',
            'type',
            'title',
            'director',
            'cast',
            'country',
            'date_added',
            'release_year',
            'rating',
            'duration',
            'listed_in',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_release_year(self, value):
        """
        Validate that release_year is within acceptable range.
        """
        if value < 1900 or value > 2030:
            raise serializers.ValidationError(
                "Release year must be between 1900 and 2030."
            )
        return value
    
    def validate_type(self, value):
        """
        Validate that type is either 'Movie' or 'TV Show'.
        """
        if value not in ['Movie', 'TV Show']:
            raise serializers.ValidationError(
                "Type must be either 'Movie' or 'TV Show'."
            )
        return value