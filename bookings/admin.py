from django.contrib import admin
from django.utils.html import format_html
from .models import Movie, Theatre, Screen, Seat, Show, Booking, BookedSeat


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'certificate', 'language', 'rating_badge', 'duration_formatted', 'is_featured', 'is_now_showing', 'release_date')
    list_filter = ('is_featured', 'is_now_showing', 'certificate', 'language', 'genres')
    search_fields = ('title', 'director', 'cast', 'genres', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_now_showing')
    ordering = ('-is_featured', '-rating', 'title')

    def rating_badge(self, obj):
        return format_html(
            '<span style="background: #e50914; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold;">★ {}</span>',
            obj.rating
        )
    rating_badge.short_description = "Rating"


class ScreenInline(admin.TabularInline):
    model = Screen
    extra = 1


@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'screens_count', 'address')
    list_filter = ('city',)
    search_fields = ('name', 'city', 'address')
    inlines = [ScreenInline]

    def screens_count(self, obj):
        return obj.screens.count()
    screens_count.short_description = "Screens"


@admin.action(description="Generate default seats for selected screens")
def generate_screen_seats(modeladmin, request, queryset):
    total_created = 0
    for screen in queryset:
        total_created += screen.generate_seats()
    modeladmin.message_user(request, f"Successfully created/verified {total_created} seats across selected screens.")


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ('name', 'theatre', 'total_rows', 'seats_per_row', 'seat_count')
    list_filter = ('theatre__city', 'theatre')
    search_fields = ('name', 'theatre__name')
    actions = [generate_screen_seats]

    def seat_count(self, obj):
        return obj.seats.count()
    seat_count.short_description = "Total Seats"


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('code', 'screen', 'theatre_name', 'tier')
    list_filter = ('tier', 'screen__theatre', 'screen')
    search_fields = ('row', 'number', 'screen__name', 'screen__theatre__name')
    ordering = ('screen', 'row', 'number')

    def theatre_name(self, obj):
        return obj.screen.theatre.name
    theatre_name.short_description = "Theatre"


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('movie', 'theatre_name', 'screen', 'date', 'formatted_time', 'format', 'language', 'pricing_summary', 'occupancy_summary', 'is_active')
    list_filter = ('date', 'format', 'language', 'is_active', 'screen__theatre')
    search_fields = ('movie__title', 'screen__name', 'screen__theatre__name')
    list_editable = ('is_active',)
    date_hierarchy = 'date'
    ordering = ('date', 'start_time')

    def theatre_name(self, obj):
        return obj.screen.theatre.name
    theatre_name.short_description = "Theatre"

    def formatted_time(self, obj):
        return obj.start_time.strftime('%I:%M %p')
    formatted_time.short_description = "Time"

    def pricing_summary(self, obj):
        return f"Std: ₹{obj.price_standard} | Prm: ₹{obj.price_premium} | VIP: ₹{obj.price_vip}"
    pricing_summary.short_description = "Pricing"

    def occupancy_summary(self, obj):
        booked = obj.booked_seats_count
        total = obj.total_seats_count
        return f"{booked}/{total} booked"
    occupancy_summary.short_description = "Seats"


class BookedSeatInline(admin.TabularInline):
    model = BookedSeat
    extra = 0
    readonly_fields = ('seat', 'price')
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'customer_name', 'movie_title', 'show_schedule', 'seats_display', 'total_amount', 'status_badge', 'created_at')
    list_filter = ('status', 'show__date', 'show__movie')
    search_fields = ('booking_reference', 'customer_name', 'customer_email', 'customer_phone', 'show__movie__title')
    readonly_fields = ('booking_reference', 'created_at', 'subtotal', 'convenience_fee', 'total_amount')
    inlines = [BookedSeatInline]
    date_hierarchy = 'created_at'

    def movie_title(self, obj):
        return obj.show.movie.title
    movie_title.short_description = "Movie"

    def show_schedule(self, obj):
        return f"{obj.show.date.strftime('%b %d')} at {obj.show.start_time.strftime('%I:%M %p')} ({obj.show.screen.theatre.name})"
    show_schedule.short_description = "Show"

    def status_badge(self, obj):
        color = "#10b981" if obj.status == "CONFIRMED" else "#ef4444"
        return format_html(
            '<span style="background: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = "Status"


@admin.register(BookedSeat)
class BookedSeatAdmin(admin.ModelAdmin):
    list_display = ('booking', 'show', 'seat', 'price')
    list_filter = ('show__movie', 'show__date')
    search_fields = ('booking__booking_reference', 'seat__row', 'seat__number')
