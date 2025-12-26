from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator

# Stores Netflix movie and TV show data
class NetflixTitle(models.Model):    
    TYPE_CHOICES = [
        ('Movie', 'Movie'),
        ('TV Show', 'TV Show'),
    ]
    
    show_id = models.CharField(max_length=20, unique=True, primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=250, validators=[MinLengthValidator(1)])
    director = models.CharField(max_length=250, blank=True, null=True)
    cast = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    date_added = models.DateField(blank=True, null=True)
    release_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2030)])
    rating = models.CharField(max_length=10, blank=True, null=True)
    duration = models.CharField(max_length=20)
    listed_in = models.TextField(validators=[MinLengthValidator(1)])
    description = models.TextField(validators=[MinLengthValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_added', '-release_year']
        verbose_name = "Netflix Title"
        verbose_name_plural = "Netflix Titles"
    
    # Returns a readable string 
    def __str__(self):
        return f"{self.title} ({self.release_year}) - {self.type}"
    
    # Splits genres string into a list
    def get_genres(self):
        return [genre.strip() for genre in self.listed_in.split(',')]
    
    # Splits cast string into a list of actor names
    def get_cast_list(self):
        if not self.cast:
            return []
        return [member.strip() for member in self.cast.split(',')]
    
    # Extracts movie duration in minutes (returns None for TV shows)
    def get_duration_minutes(self):
        if self.type == 'Movie' and 'min' in self.duration:
            return int(self.duration.split()[0])
        return None
    
    # Extracts number of seasons for TV shows (returns None for movies)
    def get_duration_seasons(self):
        if self.type == 'TV Show' and 'Season' in self.duration:
            return int(self.duration.split()[0])
        return None