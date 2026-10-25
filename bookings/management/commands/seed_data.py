from datetime import date, time, timedelta, datetime
from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from bookings.models import Movie, Theatre, Screen, Seat, Show, Booking, BookedSeat


class Command(BaseCommand):
    help = "Seeds database with demo movies, theatres, screens, shows, seats, and test users."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding CineBook database..."))

        # 1. Create Superuser and Demo User
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@cinebook.com',
                'first_name': 'CineBook',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created_admin:
            admin_user.set_password('admin1234')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin1234"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        demo_user, created_demo = User.objects.get_or_create(
            username='demouser',
            defaults={
                'email': 'demo@cinebook.com',
                'first_name': 'Alex',
                'last_name': 'Walker',
            }
        )
        if created_demo:
            demo_user.set_password('demo1234')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demouser / demo1234"))
        else:
            self.stdout.write("Demo user 'demouser' already exists.")

        # 2. Create Theatres & Screens
        theatres_data = [
            {
                'name': 'PVR ICON: Phoenix Palladium',
                'city': 'Mumbai',
                'address': '462, Senapati Bapat Marg, Lower Parel, Mumbai, Maharashtra 400013',
                'facilities': 'IMAX 3D Laser, Dolby Atmos 7.1, Luxe Recliners, Gourmet Lounge, Valet Parking',
                'screens': [
                    {'name': 'Audi 1 - IMAX Laser', 'rows': 8, 'cols': 12},
                    {'name': 'Audi 2 - Dolby Atmos P[XL]', 'rows': 8, 'cols': 12},
                ]
            },
            {
                'name': 'INOX Megaplex: Inorbit Mall',
                'city': 'Mumbai',
                'address': 'New Link Rd, Malad West, Mumbai, Maharashtra 400064',
                'facilities': 'MX4D Motion, Onyx LED Screen, Insignia Lounge, Dolby 7.1',
                'screens': [
                    {'name': 'Screen 1 - Onyx LED', 'rows': 8, 'cols': 12},
                    {'name': 'Screen 2 - MX4D Experience', 'rows': 8, 'cols': 12},
                ]
            },
            {
                'name': 'PVR IMAX: Forum South',
                'city': 'Bengaluru',
                'address': 'Konanakunte Cross, Kanakapura Rd, Bengaluru, Karnataka 560062',
                'facilities': 'IMAX with Laser, Dolby Atmos, Club Recliners, Food Studio',
                'screens': [
                    {'name': 'Audi 1 - IMAX with Laser', 'rows': 8, 'cols': 12},
                    {'name': 'Audi 2 - Dolby Atmos 4K', 'rows': 8, 'cols': 12},
                ]
            },
            {
                'name': 'Cinepolis: Orion Mall',
                'city': 'Bengaluru',
                'address': 'Dr Rajkumar Rd, Rajajinagar, Bengaluru, Karnataka 560055',
                'facilities': '4DX, VIP Lounge, RealD 3D, Dolby Surround 7.1',
                'screens': [
                    {'name': 'Screen 1 - 4DX Dynamic', 'rows': 8, 'cols': 12},
                    {'name': 'Screen 2 - Cinepolis VIP', 'rows': 8, 'cols': 12},
                ]
            },
            {
                'name': "PVR Director's Cut: Ambience Mall",
                'city': 'Delhi',
                'address': 'Nelson Mandela Marg, Vasant Kunj, New Delhi, Delhi 110070',
                'facilities': "Chef-Curated Dining, Ultra-Luxury Recliners, Dolby Atmos, Concierge Service",
                'screens': [
                    {'name': 'Screen 1 - Platinum Audi', 'rows': 8, 'cols': 12},
                    {'name': 'Screen 2 - Gold Class', 'rows': 8, 'cols': 12},
                ]
            },
        ]

        created_screens = []
        for t_info in theatres_data:
            theatre, _ = Theatre.objects.get_or_create(
                name=t_info['name'],
                defaults={
                    'city': t_info['city'],
                    'address': t_info['address'],
                    'facilities': t_info['facilities'],
                }
            )
            for s_info in t_info['screens']:
                screen, _ = Screen.objects.get_or_create(
                    theatre=theatre,
                    name=s_info['name'],
                    defaults={
                        'total_rows': s_info['rows'],
                        'seats_per_row': s_info['cols'],
                    }
                )
                seats_added = screen.generate_seats()
                created_screens.append(screen)
                if seats_added > 0:
                    self.stdout.write(f"  Generated {seats_added} seats for {theatre.name} - {screen.name}")

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(theatres_data)} Theatres and {len(created_screens)} Screens with seats."))

        # 3. Create Blockbuster Movies
        movies_data = [
            {
                'title': 'Dune: Part Two',
                'slug': 'dune-part-two',
                'description': 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the known universe, he endeavors to prevent a terrible future only he can foresee.',
                'duration_minutes': 166,
                'release_date': date(2024, 3, 1),
                'language': 'English',
                'rating': Decimal('8.9'),
                'votes_count': 94500,
                'certificate': 'U/A',
                'genres': 'Action, Adventure, Sci-Fi',
                'director': 'Denis Villeneuve',
                'cast': 'Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem, Austin Butler',
                'poster_url': 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/xOMo8BRK7PfcJv9JCnx7s5200SV.jpg',
                'trailer_youtube_id': 'Way9Dexny3w',
                'is_featured': True,
                'is_now_showing': True,
            },
            {
                'title': 'Oppenheimer',
                'slug': 'oppenheimer',
                'description': 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II under the Manhattan Project, exploring the moral and political consequences of scientific genius.',
                'duration_minutes': 180,
                'release_date': date(2023, 7, 21),
                'language': 'English',
                'rating': Decimal('8.9'),
                'votes_count': 120400,
                'certificate': 'A',
                'genres': 'Biography, Drama, History',
                'director': 'Christopher Nolan',
                'cast': 'Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr., Florence Pugh',
                'poster_url': 'https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/rLb2cwF3Pazuxaj0sRXQ037tGI1.jpg',
                'trailer_youtube_id': 'uYPbbksJxIg',
                'is_featured': True,
                'is_now_showing': True,
            },
            {
                'title': 'Spider-Man: Across the Spider-Verse',
                'slug': 'spider-man-across-the-spider-verse',
                'description': 'Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence. When heroes clash on how to handle a new threat, Miles must redefine what it means to be a hero.',
                'duration_minutes': 140,
                'release_date': date(2023, 6, 2),
                'language': 'English',
                'rating': Decimal('8.8'),
                'votes_count': 88000,
                'certificate': 'U',
                'genres': 'Animation, Action, Adventure, Sci-Fi',
                'director': 'Joaquim Dos Santos, Kemp Powers',
                'cast': 'Shameik Moore, Hailee Steinfeld, Oscar Isaac, Daniel Kaluuya',
                'poster_url': 'https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/4HodYYKEIsGOdinkGi2Ucz6X9i0.jpg',
                'trailer_youtube_id': 'cqGjhVJWtEg',
                'is_featured': True,
                'is_now_showing': True,
            },
            {
                'title': 'Interstellar: 10th Anniversary IMAX',
                'slug': 'interstellar-10th-anniversary',
                'description': 'When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers to find a new planet for humans.',
                'duration_minutes': 169,
                'release_date': date(2024, 9, 27),
                'language': 'English',
                'rating': Decimal('8.7'),
                'votes_count': 156000,
                'certificate': 'U/A',
                'genres': 'Adventure, Drama, Sci-Fi',
                'director': 'Christopher Nolan',
                'cast': 'Matthew McConaughey, Anne Hathaway, Jessica Chastain, Michael Caine',
                'poster_url': 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/xJHokMbljvjADYdit5fK5VQsXEG.jpg',
                'trailer_youtube_id': 'zSWdZVtXT7E',
                'is_featured': True,
                'is_now_showing': True,
            },
            {
                'title': 'The Dark Knight',
                'slug': 'the-dark-knight',
                'description': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.',
                'duration_minutes': 152,
                'release_date': date(2024, 5, 10),
                'language': 'English',
                'rating': Decimal('9.0'),
                'votes_count': 210000,
                'certificate': 'U/A',
                'genres': 'Action, Crime, Drama, Thriller',
                'director': 'Christopher Nolan',
                'cast': 'Christian Bale, Heath Ledger, Aaron Eckhart, Michael Caine, Gary Oldman',
                'poster_url': 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg',
                'trailer_youtube_id': 'EXeTwQWrcwY',
                'is_featured': False,
                'is_now_showing': True,
            },
            {
                'title': 'Jawan',
                'slug': 'jawan',
                'description': 'A high-octane action thriller outlining the emotional journey of a prison warden who sets out to rectify the wrongs in the society, in a bid to fulfill a promise made years ago.',
                'duration_minutes': 169,
                'release_date': date(2023, 9, 7),
                'language': 'Hindi',
                'rating': Decimal('7.8'),
                'votes_count': 64000,
                'certificate': 'U/A',
                'genres': 'Action, Thriller, Drama',
                'director': 'Atlee',
                'cast': 'Shah Rukh Khan, Nayanthara, Vijay Sethupathi, Deepika Padukone',
                'poster_url': 'https://image.tmdb.org/t/p/w500/jNQvlPkWvE0YpL2yMvV7QxX4g7e.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/628Dep6AxEtDxjZoGP78TsOxYbK.jpg',
                'trailer_youtube_id': 'MWOlnZSnXJo',
                'is_featured': False,
                'is_now_showing': True,
            },
            {
                'title': 'Inception',
                'slug': 'inception',
                'description': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project.',
                'duration_minutes': 148,
                'release_date': date(2024, 7, 16),
                'language': 'English',
                'rating': Decimal('8.8'),
                'votes_count': 180000,
                'certificate': 'U/A',
                'genres': 'Action, Sci-Fi, Adventure',
                'director': 'Christopher Nolan',
                'cast': 'Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy',
                'poster_url': 'https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/original/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg',
                'trailer_youtube_id': 'YoHD9XEInc0',
                'is_featured': False,
                'is_now_showing': True,
            },
        ]

        created_movies = []
        for m_data in movies_data:
            movie, _ = Movie.objects.update_or_create(
                slug=m_data['slug'],
                defaults=m_data
            )
            created_movies.append(movie)

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(created_movies)} Movies."))

        # 4. Create Shows for Today, Tomorrow, and +3 days
        today = date.today()
        dates_to_schedule = [today + timedelta(days=i) for i in range(5)]

        time_slots = [
            (time(10, 30), '2D', Decimal('180.00'), Decimal('260.00'), Decimal('400.00')),
            (time(14, 15), 'IMAX 3D', Decimal('240.00'), Decimal('320.00'), Decimal('500.00')),
            (time(18, 45), 'IMAX 3D', Decimal('280.00'), Decimal('380.00'), Decimal('550.00')),
            (time(22, 15), '2D', Decimal('200.00'), Decimal('280.00'), Decimal('450.00')),
        ]

        created_shows = []
        screens = list(Screen.objects.all())

        for s_date in dates_to_schedule:
            for s_idx, screen in enumerate(screens):
                # Pick 1-2 movies for this screen
                assigned_movie = created_movies[s_idx % len(created_movies)]
                for start_t, fmt, p_std, p_prm, p_vip in time_slots:
                    # Adjust format if screen is not IMAX
                    show_fmt = fmt
                    if 'IMAX' not in screen.name and fmt == 'IMAX 3D':
                        show_fmt = '3D'
                    elif '4DX' in screen.name:
                        show_fmt = '4DX'

                    show, _ = Show.objects.get_or_create(
                        screen=screen,
                        date=s_date,
                        start_time=start_t,
                        defaults={
                            'movie': assigned_movie,
                            'format': show_fmt,
                            'language': assigned_movie.language,
                            'price_standard': p_std,
                            'price_premium': p_prm,
                            'price_vip': p_vip,
                            'is_active': True,
                        }
                    )
                    created_shows.append(show)

        self.stdout.write(self.style.SUCCESS(f"Scheduled {len(created_shows)} Shows across screens and dates."))

        # 5. Create Sample Confirmed Bookings for demo_user
        # To make seat selection look real and give the user instant booking history
        if created_shows:
            sample_shows = created_shows[:4]
            for idx, show in enumerate(sample_shows):
                # Book 2-3 seats
                screen_seats = list(show.screen.seats.all())
                if len(screen_seats) >= 12:
                    # Pick row C or D
                    row_c_seats = [s for s in screen_seats if s.row == 'C']
                    chosen_seats = row_c_seats[3:6] if len(row_c_seats) >= 6 else screen_seats[4:7]

                    # Check if already booked
                    existing_booked = BookedSeat.objects.filter(show=show, seat__in=chosen_seats).exists()
                    if not existing_booked:
                        subtotal = sum(show.get_seat_price(s) for s in chosen_seats)
                        convenience_fee = Decimal('30.00') * len(chosen_seats)
                        total_amount = subtotal + convenience_fee

                        booking = Booking.objects.create(
                            user=demo_user,
                            show=show,
                            subtotal=subtotal,
                            convenience_fee=convenience_fee,
                            total_amount=total_amount,
                            status='CONFIRMED',
                            payment_method='Simulated Instant UPI (Demo)',
                            payment_status='PAID',
                            customer_name='Alex Walker',
                            customer_email='demo@cinebook.com',
                            customer_phone='+91 98765 43210',
                        )

                        for seat in chosen_seats:
                            BookedSeat.objects.create(
                                booking=booking,
                                show=show,
                                seat=seat,
                                price=show.get_seat_price(seat)
                            )
                        self.stdout.write(f"  Created sample booking {booking.booking_reference} for {show.movie.title}")

        self.stdout.write(self.style.SUCCESS("[SUCCESS] CineBook database seeded successfully! Ready to run."))
