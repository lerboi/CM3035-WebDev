import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import NetflixTitle


class Command(BaseCommand):
    help = 'Load Netflix titles from CSV file into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/netflix_titles.csv',
            help='Path to the CSV file (default: data/netflix_titles.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Netflix Data Loader'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Clear existing data if requested
        if clear_data:
            self.stdout.write('Clearing existing data...')
            count = NetflixTitle.objects.count()
            NetflixTitle.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {count} existing records'))

        # Load data from CSV
        self.stdout.write(f'\nLoading data from: {csv_file}')
        
        try:
            titles_to_create = []
            errors = []
            
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    try:
                        # Parse date_added field
                        date_added = None
                        if row['date_added'] and row['date_added'].strip():
                            try:
                                # Parse date format: "Month Day, Year" (e.g., "September 25, 2021")
                                date_added = datetime.strptime(
                                    row['date_added'].strip(), 
                                    '%B %d, %Y'
                                ).date()
                            except ValueError:
                                # If parsing fails, leave as None
                                pass
                        
                        # Create NetflixTitle instance
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
                        
                        # Show progress every 1000 records
                        if len(titles_to_create) % 1000 == 0:
                            self.stdout.write(f'  Processed {len(titles_to_create)} records...')
                    
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                        continue
            
            # Bulk create all titles
            self.stdout.write(f'\nPrepared {len(titles_to_create)} titles for import')
            self.stdout.write('Saving to database...')
            
            with transaction.atomic():
                NetflixTitle.objects.bulk_create(titles_to_create, batch_size=500)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully loaded {len(titles_to_create)} titles!'))
            
            # Show errors if any
            if errors:
                self.stdout.write(self.style.WARNING(f'\n⚠ Encountered {len(errors)} errors:'))
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(self.style.WARNING(f'  {error}'))
                if len(errors) > 10:
                    self.stdout.write(self.style.WARNING(f'  ... and {len(errors) - 10} more'))
            
            # Show summary statistics
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('SUMMARY'))
            self.stdout.write('=' * 70)
            
            total_count = NetflixTitle.objects.count()
            movie_count = NetflixTitle.objects.filter(type='Movie').count()
            tv_count = NetflixTitle.objects.filter(type='TV Show').count()
            
            self.stdout.write(f'Total titles in database: {total_count}')
            self.stdout.write(f'  Movies: {movie_count}')
            self.stdout.write(f'  TV Shows: {tv_count}')
            
            # Show sample titles
            self.stdout.write('\nSample titles loaded:')
            sample_titles = NetflixTitle.objects.all()[:5]
            for title in sample_titles:
                self.stdout.write(f'  - {title}')
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('✓ Data loading complete!'))
            self.stdout.write('=' * 70)
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: File not found: {csv_file}'))
            self.stdout.write('\nPlease ensure the CSV file exists at the specified path.')
            self.stdout.write('Expected location: data/netflix_titles.csv')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error loading data: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())