from django.urls import path
from . import views

urlpatterns = [
    # Catalog & Discovery
    path('', views.home, name='home'),
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('theatres/', views.theatres_list, name='theatres_list'),

    # Booking Journey
    path('show/<int:show_id>/seats/', views.seat_selection, name='seat_selection'),
    path('show/<int:show_id>/checkout/', views.checkout, name='checkout'),
    path('show/<int:show_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('booking/<str:booking_ref>/confirmation/', views.booking_confirmation, name='booking_confirmation'),

    # User Bookings & Profile
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<str:booking_ref>/cancel/', views.cancel_booking, name='cancel_booking'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
