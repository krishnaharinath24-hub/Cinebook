import json
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseBadRequest, JsonResponse

from .models import Movie, Theatre, Screen, Seat, Show, Booking, BookedSeat
from .forms import UserRegisterForm, UserLoginForm, CheckoutForm


def home(request):
    """Movie catalog homepage with search, genre & language filters, and featured carousel."""
    query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '').strip()
    selected_language = request.GET.get('language', '').strip()
    selected_city = request.GET.get('city', request.session.get('selected_city', 'Mumbai')).strip()
    
    # Store city preference in session
    request.session['selected_city'] = selected_city

    movies = Movie.objects.filter(is_now_showing=True)

    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(genres__icontains=query) |
            Q(director__icontains=query) |
            Q(cast__icontains=query)
        )

    if selected_genre:
        movies = movies.filter(genres__icontains=selected_genre)

    if selected_language:
        movies = movies.filter(language__iexact=selected_language)

    # City filter: only show movies that have shows in the selected city (if shows exist)
    city_shows = Show.objects.filter(screen__theatre__city__iexact=selected_city, is_active=True, date__gte=date.today())
    if city_shows.exists():
        city_movie_ids = city_shows.values_list('movie_id', flat=True).distinct()
        city_movies = movies.filter(id__in=city_movie_ids)
        # If no movies in that city match, fallback to all matching movies
        if city_movies.exists() or (query or selected_genre or selected_language):
            movies = city_movies

    featured_movies = Movie.objects.filter(is_featured=True, is_now_showing=True)[:4]
    
    # Extract distinct genres for pill filters
    all_genres = set()
    for m in Movie.objects.filter(is_now_showing=True):
        for g in m.genre_list:
            all_genres.add(g)
    sorted_genres = sorted(list(all_genres))

    distinct_languages = Movie.objects.filter(is_now_showing=True).values_list('language', flat=True).distinct()
    available_cities = Theatre.objects.values_list('city', flat=True).distinct()

    context = {
        'movies': movies,
        'featured_movies': featured_movies,
        'query': query,
        'selected_genre': selected_genre,
        'selected_language': selected_language,
        'selected_city': selected_city,
        'genres': sorted_genres,
        'languages': distinct_languages,
        'cities': available_cities,
        'total_count': movies.count(),
    }
    return render(request, 'bookings/home.html', context)


def movie_detail(request, slug):
    """Detailed movie view with trailer, cast, and showtimes organized by theatre."""
    movie = get_object_or_404(Movie, slug=slug)
    selected_city = request.session.get('selected_city', 'Mumbai')

    # Date selector: Today + next 4 days
    today = date.today()
    date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if selected_date < today:
            selected_date = today
    except ValueError:
        selected_date = today

    date_options = []
    for i in range(5):
        d = today + timedelta(days=i)
        date_options.append({
            'date': d,
            'date_str': d.strftime('%Y-%m-%d'),
            'day_name': 'Today' if i == 0 else ('Tomorrow' if i == 1 else d.strftime('%a')),
            'display_str': d.strftime('%d %b'),
            'is_selected': d == selected_date
        })

    # Fetch shows for this movie, city, and date
    shows = Show.objects.filter(
        movie=movie,
        date=selected_date,
        is_active=True
    ).select_related('screen', 'screen__theatre').order_by('screen__theatre__name', 'start_time')

    # If city filtering matches, prioritize city
    if selected_city:
        city_shows = shows.filter(screen__theatre__city__iexact=selected_city)
        if city_shows.exists():
            shows = city_shows

    # Group shows by theatre
    theatre_shows = {}
    for show in shows:
        theatre = show.screen.theatre
        if theatre not in theatre_shows:
            theatre_shows[theatre] = []
        theatre_shows[theatre].append(show)

    context = {
        'movie': movie,
        'selected_date': selected_date,
        'date_options': date_options,
        'theatre_shows': theatre_shows,
        'selected_city': selected_city,
        'available_cities': Theatre.objects.values_list('city', flat=True).distinct(),
    }
    return render(request, 'bookings/movie_detail.html', context)


def seat_selection(request, show_id):
    """Interactive cinema seat selection with live tier pricing and booked seat states."""
    show = get_object_or_404(
        Show.objects.select_related('movie', 'screen', 'screen__theatre'),
        id=show_id,
        is_active=True
    )
    screen = show.screen
    
    # Auto-generate seats for screen if not yet initialized
    if screen.seats.count() == 0:
        screen.generate_seats()

    all_seats = screen.seats.all().order_by('row', 'number')
    booked_seat_ids = show.get_booked_seat_ids()

    # Organize seats by row and tier for neat theatre layout
    rows_dict = {}
    for seat in all_seats:
        if seat.row not in rows_dict:
            rows_dict[seat.row] = {
                'row_letter': seat.row,
                'tier': seat.tier,
                'tier_name': seat.get_tier_display(),
                'price': show.get_seat_price(seat),
                'seats': []
            }
        is_booked = seat.id in booked_seat_ids
        rows_dict[seat.row]['seats'].append({
            'id': seat.id,
            'number': seat.number,
            'code': seat.code,
            'tier': seat.tier,
            'price': float(show.get_seat_price(seat)),
            'is_booked': is_booked,
            'status': 'booked' if is_booked else 'available'
        })

    # Group rows by tier sections (VIP, Premium, Standard)
    sections = {}
    for row_letter, row_data in rows_dict.items():
        tier = row_data['tier']
        if tier not in sections:
            sections[tier] = {
                'name': row_data['tier_name'],
                'price': row_data['price'],
                'rows': []
            }
        sections[tier]['rows'].append(row_data)

    context = {
        'show': show,
        'sections': sections,
        'booked_seat_ids_json': json.dumps(list(booked_seat_ids)),
        'price_map_json': json.dumps({
            'STANDARD': float(show.price_standard),
            'PREMIUM': float(show.price_premium),
            'VIP': float(show.price_vip),
        }),
        'convenience_fee_per_ticket': 30.00,
    }
    return render(request, 'bookings/seat_selection.html', context)


@login_required(login_url='login')
def checkout(request, show_id):
    """Review booking summary, customer details, and mock payment gateway."""
    show = get_object_or_404(
        Show.objects.select_related('movie', 'screen', 'screen__theatre'),
        id=show_id,
        is_active=True
    )

    seat_ids_str = request.POST.get('seat_ids') or request.GET.get('seats', '')
    if not seat_ids_str:
        messages.error(request, "Please select at least one seat before proceeding to checkout.")
        return redirect('seat_selection', show_id=show.id)

    try:
        seat_ids = [int(s.strip()) for s in seat_ids_str.split(',') if s.strip()]
    except ValueError:
        messages.error(request, "Invalid seat selection format.")
        return redirect('seat_selection', show_id=show.id)

    if not seat_ids:
        messages.error(request, "Please select at least one seat.")
        return redirect('seat_selection', show_id=show.id)

    # Server-side validation of seats:
    # 1. Seats must belong to the screen
    seats = Seat.objects.filter(screen=show.screen, id__in=seat_ids).order_by('row', 'number')
    if seats.count() != len(seat_ids):
        messages.error(request, "One or more selected seats are invalid for this screen.")
        return redirect('seat_selection', show_id=show.id)

    # 2. Check if already booked
    already_booked = BookedSeat.objects.filter(
        show=show,
        seat__in=seats,
        booking__status='CONFIRMED'
    ).select_related('seat')

    if already_booked.exists():
        clash_names = ", ".join([bs.seat.code for bs in already_booked])
        messages.error(request, f"Sorry! Seat(s) {clash_names} were just booked by another customer. Please choose different seats.")
        return redirect('seat_selection', show_id=show.id)

    # Calculate true price on server
    seat_breakdown = []
    subtotal = Decimal('0.00')
    for seat in seats:
        seat_price = show.get_seat_price(seat)
        subtotal += seat_price
        seat_breakdown.append({
            'seat': seat,
            'price': seat_price,
            'tier': seat.get_tier_display(),
        })

    convenience_fee = Decimal('30.00') * len(seats)
    total_amount = subtotal + convenience_fee

    initial_data = {
        'customer_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'customer_email': request.user.email,
        'seat_ids': ",".join(str(s) for s in seat_ids),
    }
    form = CheckoutForm(initial=initial_data)

    context = {
        'show': show,
        'seats': seats,
        'seat_breakdown': seat_breakdown,
        'subtotal': subtotal,
        'convenience_fee': convenience_fee,
        'total_amount': total_amount,
        'seat_ids_str': ",".join(str(s) for s in seat_ids),
        'form': form,
    }
    return render(request, 'bookings/checkout.html', context)


@login_required(login_url='login')
def confirm_booking(request, show_id):
    """
    Handles payment submission and securely completes ticket booking with database locking and constraints.
    Server strictly re-validates seat availability and calculates all prices.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")

    show = get_object_or_404(
        Show.objects.select_related('movie', 'screen', 'screen__theatre'),
        id=show_id,
        is_active=True
    )

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please correct the errors in the checkout form.")
        return redirect('seat_selection', show_id=show.id)

    cleaned_seat_ids = form.cleaned_data['seat_ids']
    customer_name = form.cleaned_data['customer_name']
    customer_email = form.cleaned_data['customer_email']
    customer_phone = form.cleaned_data['customer_phone']
    payment_method = form.cleaned_data['payment_method']

    # Atomic transaction with concurrency check
    try:
        with transaction.atomic():
            # Validate seats belong to this screen
            seats = list(Seat.objects.filter(screen=show.screen, id__in=cleaned_seat_ids).select_for_update())
            if len(seats) != len(cleaned_seat_ids):
                messages.error(request, "Invalid seat selection detected.")
                return redirect('seat_selection', show_id=show.id)

            # Check for conflict in confirmed booked seats
            conflicting_bookings = BookedSeat.objects.filter(
                show=show,
                seat__in=seats,
                booking__status='CONFIRMED'
            ).select_related('seat')

            if conflicting_bookings.exists():
                booked_codes = ", ".join([bs.seat.code for bs in conflicting_bookings])
                messages.error(request, f"Seat(s) {booked_codes} have just been booked. Please pick other seats.")
                return redirect('seat_selection', show_id=show.id)

            # Strictly recalculate pricing on the server
            subtotal = sum(show.get_seat_price(seat) for seat in seats)
            convenience_fee = Decimal('30.00') * len(seats)
            total_amount = subtotal + convenience_fee

            # Create confirmed booking
            booking = Booking.objects.create(
                user=request.user,
                show=show,
                subtotal=subtotal,
                convenience_fee=convenience_fee,
                total_amount=total_amount,
                status='CONFIRMED',
                payment_method=dict(form.fields['payment_method'].choices).get(payment_method, 'Instant Pay (Demo)'),
                payment_status='PAID',
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
            )

            # Create BookedSeat records (guaranteed unique by DB constraint)
            booked_seat_objs = [
                BookedSeat(
                    booking=booking,
                    show=show,
                    seat=seat,
                    price=show.get_seat_price(seat)
                )
                for seat in seats
            ]
            BookedSeat.objects.bulk_create(booked_seat_objs)

        messages.success(request, f"Booking successful! Your confirmation code is {booking.booking_reference}.")
        return redirect('booking_confirmation', booking_ref=booking.booking_reference)

    except IntegrityError:
        messages.error(request, "One of your chosen seats was booked at the exact same moment. Please select another seat.")
        return redirect('seat_selection', show_id=show.id)
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during booking: {str(e)}")
        return redirect('seat_selection', show_id=show.id)


@login_required(login_url='login')
def booking_confirmation(request, booking_ref):
    """View digital ticket with QR code, booking reference, and show details. Users can only view their own."""
    booking = get_object_or_404(
        Booking.objects.select_related('show', 'show__movie', 'show__screen', 'show__screen__theatre'),
        booking_reference=booking_ref,
        user=request.user  # Strict ownership check
    )

    booked_seats = booking.booked_seats.select_related('seat').all()

    context = {
        'booking': booking,
        'booked_seats': booked_seats,
        'show': booking.show,
        'movie': booking.show.movie,
        'theatre': booking.show.screen.theatre,
    }
    return render(request, 'bookings/booking_confirmation.html', context)


@login_required(login_url='login')
def my_bookings(request):
    """Lists all past and upcoming bookings for the authenticated user."""
    bookings = Booking.objects.filter(user=request.user).select_related(
        'show', 'show__movie', 'show__screen', 'show__screen__theatre'
    ).prefetch_related('booked_seats__seat').order_by('-created_at')

    upcoming_bookings = [b for b in bookings if b.status == 'CONFIRMED' and not b.show.is_past]
    past_bookings = [b for b in bookings if b.status == 'CANCELLED' or b.show.is_past]

    context = {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'total_bookings': bookings.count(),
    }
    return render(request, 'bookings/my_bookings.html', context)


@login_required(login_url='login')
def cancel_booking(request, booking_ref):
    """Cancels an upcoming confirmed booking and releases the reserved seats."""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")

    booking = get_object_or_404(Booking, booking_reference=booking_ref, user=request.user)

    if not booking.can_cancel:
        messages.error(request, "This booking cannot be cancelled (show has either passed or booking was already cancelled).")
        return redirect('my_bookings')

    with transaction.atomic():
        # Release the seats by deleting BookedSeat entries or updating status
        booking.booked_seats.all().delete()
        booking.status = 'CANCELLED'
        booking.save()

    messages.success(request, f"Booking {booking.booking_reference} has been cancelled. A simulated refund of ₹{booking.total_amount} has been initiated.")
    return redirect('my_bookings')


def theatres_list(request):
    """Lists theatres and their facilities with city filtering."""
    selected_city = request.GET.get('city', request.session.get('selected_city', 'All')).strip()
    theatres = Theatre.objects.all().prefetch_related('screens')

    if selected_city and selected_city != 'All':
        theatres = theatres.filter(city__iexact=selected_city)

    cities = Theatre.objects.values_list('city', flat=True).distinct()

    context = {
        'theatres': theatres,
        'cities': cities,
        'selected_city': selected_city,
    }
    return render(request, 'bookings/theatres_list.html', context)


def register_view(request):
    """User registration view with automatic sign-in upon success."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Log user in
            login(request, user)
            messages.success(request, f"Welcome to CineBook, {user.first_name or user.username}! Your account has been created.")
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
    else:
        form = UserRegisterForm()

    return render(request, 'bookings/auth_register.html', {'form': form})


def login_view(request):
    """User login view with return redirection support."""
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next') or 'home'

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'bookings/auth_login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """Logs out the user and redirects to homepage."""
    logout(request)
    messages.info(request, "You have been logged out securely. See you soon!")
    return redirect('home')
