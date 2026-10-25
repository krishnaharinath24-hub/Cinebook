import uuid
from datetime import datetime, date, time
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class Movie(models.Model):
    CERTIFICATE_CHOICES = [
        ('U', 'U (Universal)'),
        ('U/A', 'U/A (Parental Guidance for under 12)'),
        ('A', 'A (Adults Only)'),
        ('PG-13', 'PG-13 (Parents Strongly Cautioned)'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(help_text="Synopsis and storyline")
    duration_minutes = models.PositiveIntegerField(help_text="Runtime in minutes (e.g. 152)")
    release_date = models.DateField(default=date.today)
    language = models.CharField(max_length=60, default="English")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=8.5, help_text="Rating out of 10")
    votes_count = models.PositiveIntegerField(default=15400, help_text="Number of user ratings")
    certificate = models.CharField(max_length=10, choices=CERTIFICATE_CHOICES, default='U/A')
    genres = models.CharField(max_length=160, help_text="Comma-separated genres, e.g. Action, Sci-Fi, Adventure")
    director = models.CharField(max_length=120)
    cast = models.CharField(max_length=255, help_text="Lead cast members, comma-separated")
    poster_url = models.URLField(max_length=500, blank=True, help_text="Movie poster image URL")
    banner_url = models.URLField(max_length=500, blank=True, help_text="Hero backdrop image URL")
    trailer_youtube_id = models.CharField(max_length=50, blank=True, help_text="YouTube Video ID (e.g. 'd9MyW72ELq0')")
    is_featured = models.BooleanField(default=False, help_text="Display in top banner carousel")
    is_now_showing = models.BooleanField(default=True, help_text="Currently running in cinemas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-rating', 'title']

    def __str__(self):
        return f"{self.title} ({self.language})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "movie"
            slug = base_slug
            counter = 1
            while Movie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def duration_formatted(self):
        hours = self.duration_minutes // 60
        mins = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    @property
    def genre_list(self):
        return [g.strip() for g in self.genres.split(',') if g.strip()]

    @property
    def trailer_embed_url(self):
        if self.trailer_youtube_id:
            return f"https://www.youtube.com/embed/{self.trailer_youtube_id}?autoplay=1&mute=0"
        return ""


class Theatre(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=80, default="Mumbai")
    address = models.TextField()
    facilities = models.CharField(
        max_length=255,
        default="Dolby Atmos 7.1, 4K Laser Projection, Recliner Seats, Gourmet Food Court, Valet Parking"
    )

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def facility_list(self):
        return [f.strip() for f in self.facilities.split(',') if f.strip()]


class Screen(models.Model):
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=80, help_text="e.g. Audi 1 - IMAX 3D")
    total_rows = models.PositiveIntegerField(default=8, help_text="Number of rows (A to H)")
    seats_per_row = models.PositiveIntegerField(default=12, help_text="Number of seats per row (1 to 12)")

    class Meta:
        ordering = ['theatre', 'name']
        unique_together = ('theatre', 'name')

    def __str__(self):
        return f"{self.theatre.name} - {self.name}"

    def generate_seats(self):
        """Generates Seat records for this screen if they do not exist already."""
        row_letters = [chr(65 + i) for i in range(min(self.total_rows, 26))]
        created_count = 0

        for r_idx, row in enumerate(row_letters):
            # Tier assignment:
            # First 2 rows (A, B): Standard
            # Middle rows: Premium
            # Last 2 rows: VIP Recliner
            if r_idx < 2:
                tier = 'STANDARD'
            elif r_idx >= len(row_letters) - 2:
                tier = 'VIP'
            else:
                tier = 'PREMIUM'

            for num in range(1, self.seats_per_row + 1):
                _, created = Seat.objects.get_or_create(
                    screen=self,
                    row=row,
                    number=num,
                    defaults={'tier': tier}
                )
                if created:
                    created_count += 1
        return created_count


class Seat(models.Model):
    TIER_CHOICES = [
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
        ('VIP', 'VIP Recliner'),
    ]

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=2)
    number = models.PositiveIntegerField()
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='STANDARD')

    class Meta:
        ordering = ['row', 'number']
        unique_together = ('screen', 'row', 'number')

    def __str__(self):
        return f"{self.screen.name} - {self.row}{self.number} ({self.get_tier_display()})"

    @property
    def code(self):
        return f"{self.row}{self.number}"


class Show(models.Model):
    FORMAT_CHOICES = [
        ('2D', '2D'),
        ('3D', '3D'),
        ('IMAX 3D', 'IMAX 3D'),
        ('4DX', '4DX'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='shows')
    date = models.DateField(default=date.today)
    start_time = models.TimeField()
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='2D')
    language = models.CharField(max_length=50, default='English')
    price_standard = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('180.00'))
    price_premium = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('260.00'))
    price_vip = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('420.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('screen', 'date', 'start_time')

    def __str__(self):
        return f"{self.movie.title} at {self.screen} on {self.date} {self.start_time.strftime('%I:%M %p')}"

    def get_price_for_tier(self, tier):
        tier = tier.upper()
        if tier == 'VIP':
            return self.price_vip
        elif tier == 'PREMIUM':
            return self.price_premium
        return self.price_standard

    def get_seat_price(self, seat):
        return self.get_price_for_tier(seat.tier)

    def get_booked_seat_ids(self):
        """Returns set of Seat IDs booked and confirmed for this show."""
        return set(
            BookedSeat.objects.filter(
                show=self,
                booking__status='CONFIRMED'
            ).values_list('seat_id', flat=True)
        )

    @property
    def total_seats_count(self):
        return self.screen.seats.count()

    @property
    def booked_seats_count(self):
        return BookedSeat.objects.filter(show=self, booking__status='CONFIRMED').count()

    @property
    def available_seats_count(self):
        return max(0, self.total_seats_count - self.booked_seats_count)

    @property
    def is_past(self):
        show_datetime = timezone.make_aware(datetime.combine(self.date, self.start_time))
        return show_datetime < timezone.now()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey(Show, on_delete=models.PROTECT, related_name='bookings')
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)
    convenience_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('30.00'))
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    payment_method = models.CharField(max_length=60, default="Simulated Instant Pay (Demo)")
    payment_status = models.CharField(max_length=20, default="PAID")
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ref: {self.booking_reference} - {self.show.movie.title} ({self.customer_name})"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            # Generate e.g. CB-7D9A2F
            ref = f"CB-{uuid.uuid4().hex[:8].upper()}"
            while Booking.objects.filter(booking_reference=ref).exists():
                ref = f"CB-{uuid.uuid4().hex[:8].upper()}"
            self.booking_reference = ref
        super().save(*args, **kwargs)

    @property
    def seats_display(self):
        seat_codes = [bs.seat.code for bs in self.booked_seats.select_related('seat').all()]
        return ", ".join(seat_codes) if seat_codes else "None"

    @property
    def can_cancel(self):
        """Allow cancellation if status is CONFIRMED and show is in the future."""
        if self.status != 'CONFIRMED':
            return False
        show_dt = timezone.make_aware(datetime.combine(self.show.date, self.show.start_time))
        return show_dt > timezone.now()


class BookedSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booked_seats')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='booked_seats')
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name='show_bookings')
    price = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        # Crucial database constraint: No duplicate bookings for the same show and seat!
        unique_together = ('show', 'seat')

    def __str__(self):
        return f"{self.show.movie.title} - {self.seat.code} (${self.price})"
