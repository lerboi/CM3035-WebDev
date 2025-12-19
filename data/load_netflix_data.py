import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import NetflixTitle

class Command(BaseCommand):    
    help = 'Load Netflix titles from CSV file into database'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='data/netflix_titles.csv', help='Path to CSV file')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before loading')

    # Main function that runs when command is executed
    def handle(self, *args, **options):
        csv_file = options['file']
        
        if options['clear']:
            count = NetflixTitle.objects.count()
            NetflixTitle.objects.all().delete()
            self.stdout.write(f'Deleted {count} existing records')

        self.stdout.write(f'Loading data from: {csv_file}')
        
        try:
            titles_to_create = []
            errors = []
            
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Parse date from Month Day, Year format
                        date_added = None
                        if row['date_added'] and row['date_added'].strip():
                            try:
                                date_added = datetime.strptime(row['date_added'].strip(), '%B %d, %Y').date()
                            except ValueError:
                                pass
                        
                        title = NetflixTitle(
                            show_id=row['show_id'].strip(),
                            type=row['type'].strip(),
                            title=row['title'].strip(),
                            director=row['director'].strip() if row['director'].strip() else None,
                            cast=row['cast'].strip() if row['cast'].strip() else None,
                            country=row['country'].strip() if row['country'].strip() else None,
                            date_added=date_added,
                            release_year=int(row['release_year']),
                            rating=row['rating'].strip() if row['rating'].strip() else None,
                            duration=row['duration'].strip(),
                            listed_in=row['listed_in'].strip(),
                            description=row['description'].strip()
                        )
                        titles_to_create.append(title)
                        
                        if len(titles_to_create) % 1000 == 0:
                            self.stdout.write(f'  Processed {len(titles_to_create)} records...')
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
            
            # Bulk insert all records
            with transaction.atomic():
                NetflixTitle.objects.bulk_create(titles_to_create, batch_size=500)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(titles_to_create)} titles'))
            
            if errors:
                self.stdout.write(self.style.WARNING(f'Errors: {len(errors)}'))
                for error in errors[:5]:
                    self.stdout.write(f'  {error}')
            
            # Show summary
            self.stdout.write(f'\nTotal: {NetflixTitle.objects.count()}')
            self.stdout.write(f'Movies: {NetflixTitle.objects.filter(type="Movie").count()}')
            self.stdout.write(f'TV Shows: {NetflixTitle.objects.filter(type="TV Show").count()}')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))