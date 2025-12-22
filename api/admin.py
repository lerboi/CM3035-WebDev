from django.contrib import admin
from .models import NetflixTitle


@admin.register(NetflixTitle)
class NetflixTitleAdmin(admin.ModelAdmin):    
    list_display = ('show_id', 'title', 'type', 'release_year', 'rating', 'date_added')
    list_filter = ('type', 'rating', 'release_year')
    search_fields = ('title', 'director', 'cast', 'description')
    ordering = ('-date_added', '-release_year')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {'fields': ('show_id', 'type', 'title')}),
        ('Production Details', {'fields': ('director', 'cast', 'country')}),
        ('Release Information', {'fields': ('release_year', 'date_added', 'rating', 'duration')}),
        ('Content Details', {'fields': ('listed_in', 'description')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )