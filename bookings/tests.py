from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
from bookings.models import Movie, Theatre, Screen, Seat, Show, Booking, BookedSeat


class CineBookModelAndBookingTests(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
            first_name='Alice',
            last_name='Smith'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123',
            first_name='Bob',
            last_name='Jones'
        )

        # Create Theatre & Screen
        self.theatre = Theatre.objects.create(
            name='CineBook IMAX Grand',
            city='Mumbai',
            address='100 Marine Drive',
            facilities='IMAX 3D, Dolby Atmos'
        )
        self.screen = Screen.objects.create(
            theatre=self.theatre,
            name='Audi 1 - IMAX',
            total_rows=4,
            seats_per_row=6
        )
        # Generate seats (4 rows x 6 cols = 24 seats)
        self.screen.generate_seats()

        # Create Movie
        self.movie = Movie.objects.create(
            title='Cosmic Horizon',
            description='An epic sci-fi space expedition.',
            duration_minutes=150,
            release_date=date.today(),
            language='English',
            rating=Decimal('9.1'),
            certificate='U/A',
            genres='Sci-Fi, Adventure',
            director='Christopher Nolan',
            cast='Matthew McConaughey, Anne Hathaway',
            is_now_showing=True
        )

        # Create Show for tomorrow
        tomorrow = date.today() + timedelta(days=1)
        self.show = Show.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=tomorrow,
            start_time=time(18, 30),
            format='IMAX 3D',
            language='English',
            price_standard=Decimal('180.00'),
            price_premium=Decimal('260.00'),
            price_vip=Decimal('420.00')
        )

        self.client = Client()

    def test_screen_seat_generation(self):
        """Verify that screen.generate_seats creates the expected number of seats with proper tier distribution."""
        seats = Seat.objects.filter(screen=self.screen)
        self.assertEqual(seats.count(), 24)
        
        # Check rows A to D
        row_letters = set(seats.values_list('row', flat=True))
        self.assertEqual(row_letters, {'A', 'B', 'C', 'D'})

        # Row A should be STANDARD
        row_a_seat = seats.filter(row='A', number=1).first()
        self.assertEqual(row_a_seat.tier, 'STANDARD')
        self.assertEqual(self.show.get_seat_price(row_a_seat), Decimal('180.00'))

        # Row D should be VIP
        row_d_seat = seats.filter(row='D', number=1).first()
        self.assertEqual(row_d_seat.tier, 'VIP')
        self.assertEqual(self.show.get_seat_price(row_d_seat), Decimal('420.00'))

    def test_movie_slug_auto_generation(self):
        """Verify that slug is automatically created from movie title."""
        self.assertEqual(self.movie.slug, 'cosmic-horizon')

    def test_login_required_for_checkout_and_confirmation(self):
        """Verify unauthenticated users are redirected to login when attempting checkout."""
        seat = Seat.objects.filter(screen=self.screen).first()
        response = self.client.get(reverse('checkout', kwargs={'show_id': self.show.id}) + f"?seats={seat.id}")
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_successful_booking_flow(self):
        """Verify authenticated user can book seats with server-side price calculation and unique reference."""
        self.client.login(username='alice', password='password123')
        seats_to_book = list(Seat.objects.filter(screen=self.screen, row='A')[:2])
        seat_ids_str = f"{seats_to_book[0].id},{seats_to_book[1].id}"

        response = self.client.post(
            reverse('confirm_booking', kwargs={'show_id': self.show.id}),
            data={
                'seat_ids': seat_ids_str,
                'customer_name': 'Alice Smith',
                'customer_email': 'alice@example.com',
                'customer_phone': '9876543210',
                'payment_method': 'SIMULATED_UPI',
            }
        )

        # Successful booking redirects to confirmation
        self.assertEqual(response.status_code, 302)
        self.assertIn('/confirmation/', response.url)

        # Verify Booking in database
        booking = Booking.objects.filter(user=self.user1).first()
        self.assertIsNotNone(booking)
        self.assertTrue(booking.booking_reference.startswith('CB-'))
        self.assertEqual(booking.status, 'CONFIRMED')
        
        # Pricing check: 2 Standard seats (2 * 180 = 360) + fee (2 * 30 = 60) = 420
        self.assertEqual(booking.subtotal, Decimal('360.00'))
        self.assertEqual(booking.convenience_fee, Decimal('60.00'))
        self.assertEqual(booking.total_amount, Decimal('420.00'))

        # Verify BookedSeat records created
        self.assertEqual(booking.booked_seats.count(), 2)

    def test_prevent_duplicate_seat_booking(self):
        """Verify server prevents double-booking of seats for the same show."""
        self.client.login(username='alice', password='password123')
        seat = Seat.objects.filter(screen=self.screen, row='B', number=1).first()

        # Alice books seat B1
        self.client.post(
            reverse('confirm_booking', kwargs={'show_id': self.show.id}),
            data={
                'seat_ids': str(seat.id),
                'customer_name': 'Alice Smith',
                'customer_email': 'alice@example.com',
                'customer_phone': '9876543210',
                'payment_method': 'SIMULATED_UPI',
            }
        )

        # Now Bob attempts to book the same seat B1
        self.client.login(username='bob', password='password123')
        response = self.client.post(
            reverse('confirm_booking', kwargs={'show_id': self.show.id}),
            data={
                'seat_ids': str(seat.id),
                'customer_name': 'Bob Jones',
                'customer_email': 'bob@example.com',
                'customer_phone': '9123456789',
                'payment_method': 'SIMULATED_CARD',
            }
        )

        # Bob should be redirected back to seat selection with an error message
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/show/{self.show.id}/seats/", response.url)

        # Verify Bob does not have a booking
        self.assertEqual(Booking.objects.filter(user=self.user2).count(), 0)

        # Verify database constraint also forbids direct duplicate insert
        with self.assertRaises(IntegrityError):
            BookedSeat.objects.create(
                booking=Booking.objects.first(),
                show=self.show,
                seat=seat,
                price=Decimal('180.00')
            )

    def test_user_cannot_view_others_booking(self):
        """Verify that user cannot view another user's booking confirmation."""
        # Alice books a ticket
        self.client.login(username='alice', password='password123')
        seat = Seat.objects.filter(screen=self.screen, row='C', number=1).first()
        self.client.post(
            reverse('confirm_booking', kwargs={'show_id': self.show.id}),
            data={
                'seat_ids': str(seat.id),
                'customer_name': 'Alice Smith',
                'customer_email': 'alice@example.com',
                'customer_phone': '9876543210',
                'payment_method': 'SIMULATED_UPI',
            }
        )
        alice_booking = Booking.objects.filter(user=self.user1).first()

        # Bob logs in and tries to access Alice's booking confirmation
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('booking_confirmation', kwargs={'booking_ref': alice_booking.booking_reference}))
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)

    def test_cancel_booking_releases_seats(self):
        """Verify that cancelling an upcoming booking releases seats for other users."""
        self.client.login(username='alice', password='password123')
        seat = Seat.objects.filter(screen=self.screen, row='C', number=2).first()

        self.client.post(
            reverse('confirm_booking', kwargs={'show_id': self.show.id}),
            data={
                'seat_ids': str(seat.id),
                'customer_name': 'Alice Smith',
                'customer_email': 'alice@example.com',
                'customer_phone': '9876543210',
                'payment_method': 'SIMULATED_UPI',
            }
        )
        booking = Booking.objects.filter(user=self.user1).first()
        self.assertIn(seat.id, self.show.get_booked_seat_ids())

        # Cancel the booking
        cancel_response = self.client.post(reverse('cancel_booking', kwargs={'booking_ref': booking.booking_reference}))
        self.assertEqual(cancel_response.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        # Seat must be released and no longer in booked seat IDs
        self.assertNotIn(seat.id, self.show.get_booked_seat_ids())

    def test_pages_render_without_errors(self):
        """Verify that all main pages render with HTTP 200 and expected template context."""
        # 1. Homepage
        res_home = self.client.get(reverse('home'))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, 'Cosmic Horizon')
        self.assertContains(res_home, 'CineBook')

        # 2. Movie Detail (query for show's date)
        show_date_str = self.show.date.strftime('%Y-%m-%d')
        res_movie = self.client.get(reverse('movie_detail', kwargs={'slug': self.movie.slug}) + f"?date={show_date_str}")
        self.assertEqual(res_movie.status_code, 200)
        self.assertContains(res_movie, 'Cosmic Horizon')
        self.assertContains(res_movie, 'CineBook IMAX Grand')


        # 3. Theatres List
        res_theatres = self.client.get(reverse('theatres_list'))
        self.assertEqual(res_theatres.status_code, 200)
        self.assertContains(res_theatres, 'CineBook IMAX Grand')

        # 4. Seat Selection
        res_seats = self.client.get(reverse('seat_selection', kwargs={'show_id': self.show.id}))
        self.assertEqual(res_seats.status_code, 200)
        self.assertContains(res_seats, 'CINEMA SCREEN')
        self.assertContains(res_seats, 'Booking Summary')

        # 5. Auth pages
        res_login = self.client.get(reverse('login'))
        self.assertEqual(res_login.status_code, 200)
        self.assertContains(res_login, 'Sign In')

        res_register = self.client.get(reverse('register'))
        self.assertEqual(res_register.status_code, 200)
        self.assertContains(res_register, 'Create Your Account')

        # 6. My Bookings (authenticated)
        self.client.login(username='alice', password='password123')
        res_my_bookings = self.client.get(reverse('my_bookings'))
        self.assertEqual(res_my_bookings.status_code, 200)
        self.assertContains(res_my_bookings, 'My Bookings')

