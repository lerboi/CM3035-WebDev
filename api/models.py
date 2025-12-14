from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator

# Create your models here.

class NetflixTitle(models.Model):
    """
    Model representing a Netflix movie or TV show.
    
    This model stores comprehensive metadata about Netflix content including
    title information, release details, ratings, and categorization.
    """
    
    # Type choices for content
    TYPE_CHOICES = [
        ('Movie', 'Movie'),
        ('TV Show', 'TV Show'),
    ]
    
    # Primary identification
    show_id = models.CharField(
        max_length=20,
        unique=True,
        primary_key=True,
        help_text="Unique identifier for this title"
    )
    
    # Content type and title
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type of content: Movie or TV Show"
    )
    
    title = models.CharField(
        max_length=250,
        validators=[MinLengthValidator(1)],
        help_text="Title of the movie or TV show"
    )
    
    # Production details
    director = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text="Director(s) - comma-separated if multiple"
    )
    
    cast = models.TextField(
        blank=True,
        null=True,
        help_text="Cast members - comma-separated list"
    )
    
    country = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Country/countries of production - comma-separated if multiple"
    )
    
    # Temporal information
    date_added = models.DateField(
        blank=True,
        null=True,
        help_text="Date when content was added to Netflix"
    )
    
    release_year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2030)
        ],
        help_text="Original release year of the content"
    )
    
    # Content classification
    rating = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Content rating (e.g., TV-MA, PG-13, R)"
    )
    
    duration = models.CharField(
        max_length=20,
        help_text="Duration - minutes for movies, seasons for TV shows"
    )
    
    # Categorization and description
    listed_in = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text="Genres/categories - comma-separated list"
    )
    
    description = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text="Brief description or synopsis"
    )
    
    # Metadata (optional but recommended)
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created in our database"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    
    class Meta:
        ordering = ['-date_added', '-release_year']
        verbose_name = "Netflix Title"
        verbose_name_plural = "Netflix Titles"
    
    def __str__(self):
        """String representation of the model"""
        return f"{self.title} ({self.release_year}) - {self.type}"
    
    def get_genres(self):
        """
        Helper method to get list of genres.
        Returns list of genre strings.
        """
        return [genre.strip() for genre in self.listed_in.split(',')]
    
    def get_cast_list(self):
        """
        Helper method to get list of cast members.
        Returns list of cast member names or empty list if no cast.
        """
        if not self.cast:
            return []
        return [member.strip() for member in self.cast.split(',')]
    
    def get_duration_minutes(self):
        """
        Helper method to extract duration in minutes for movies.
        Returns integer or None if not a movie.
        """
        if self.type == 'Movie' and 'min' in self.duration:
            return int(self.duration.split()[0])
        return None
    
    def get_duration_seasons(self):
        """
        Helper method to extract number of seasons for TV shows.
        Returns integer or None if not a TV show.
        """
        if self.type == 'TV Show' and 'Season' in self.duration:
            return int(self.duration.split()[0])
        return None