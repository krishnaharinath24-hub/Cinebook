# CineBook 🎬 — Movie Ticket Booking Platform

**CineBook** is a full-featured, modern movie ticket booking web application inspired by **BookMyShow**, built with **Python**, **Django**, **SQLite**, **HTML5**, **Vanilla CSS**, and **Vanilla JavaScript**.

It delivers a sleek dark-mode UI with vibrant red accents, interactive cinema seat selection, live price computation, server-side concurrency safeguards, user authentication, e-ticket generation with QR codes, and a comprehensive Django administration portal.

---

## 🌟 Key Features

1. **Movie Discovery & Homepage**:
   - Dynamic Hero Banner with featured blockbuster movies.
   - Live search by movie title, director, cast, and genres.
   - Multi-category filtering: Genre pills (Action, Sci-Fi, Adventure, Drama) and Language pills.
   - City selector (Mumbai, Bengaluru, Delhi) with session persistence.
   - Movie cards with high-definition posters, rating badges, duration, certificate, and formats (IMAX, 2D, 4DX).

2. **Movie Detail & Showtimes**:
   - Comprehensive movie synopsis, director, and lead cast information.
   - Integrated YouTube trailer player modal with zero external paid APIs.
   - Interactive 5-day date picker (Today, Tomorrow, and upcoming dates).
   - Showtimes grouped by theatre with formats, starting prices, and availability indicators (*Filling Fast* vs *Available*).

3. **Interactive Cinema Seat Selection**:
   - Realistic cinema hall layout with curved glowing screen indicator (*Screen: All Eyes This Way*).
   - Multi-tier seat pricing:
     - **VIP Recliners** (Rows G & H) — Luxury recliners with premium pricing.
     - **Premium Seats** (Rows C to F) — Optimal viewing section.
     - **Standard Seats** (Rows A & B) — Front row value seats.
   - Visual states: **Available**, **Selected** (crimson red glow), and **Sold/Booked** (disabled).
   - Live sidebar calculation: Selected seat chips, ticket count, ticket subtotal, convenience fee, and grand total.
   - Selection limit: Maximum 10 seats per booking.

4. **Booking Correctness & Security**:
   - **Login Required**: Unauthenticated users are seamlessly directed to login before checkout and return to their flow.
   - **Server-Side Validation**: Never trusts prices, subtotal, or seat availability sent by client JavaScript. All pricing is recalculated from database models.
   - **Concurrency & Double-Booking Prevention**: Uses `transaction.atomic()` and a strict database constraint `unique_together = ('show', 'seat')` on `BookedSeat` to guarantee that no two users can book the same seat for the same show.
   - **Ownership Isolation**: Users can only view and manage tickets associated with their own account.
   - **CSRF Protection**: All state-changing requests use Django's CSRF token protection.
   - **Demo Payment Gateway**: Simulated payment methods (*Instant FastPay UPI*, *Card Demo*, *Pay at Box Office*) without storing sensitive card details.

5. **Digital E-Tickets & Confirmation**:
   - Digital cinema ticket with tear-away perforated divider.
   - Unique alphanumeric booking reference (e.g. `CB-7D9A2F41`).
   - Clean SVG vector QR code for turnstile entry verification.
   - One-click **Print / Download Ticket** functionality.

6. **User Account Management & My Bookings**:
   - User registration with validation, secure password hashing, and instant login.
   - Login and logout with return redirection support.
   - **My Bookings Dashboard**: Categorized into *Upcoming Reservations* and *Booking History / Completed*.
   - **Cancellation Support**: Allows users to cancel upcoming confirmed bookings, releasing reserved seats back into the available pool.

7. **Django Admin Portal**:
   - Pre-configured admin dashboard for managing Movies, Theatres, Screens, Seats, Shows, and Bookings.
   - Screen action: "Generate default seats for selected screens".
   - Search, filters, date hierarchies, and status badges.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Django 6.0+
- **Environment**: python-dotenv (Twelve-Factor configuration via `.env`)
- **Database**: SQLite (built-in; zero configuration needed for development)
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Design System with CSS variables), Vanilla JavaScript (ES6+)
- **Typography**: Google Fonts (*Outfit* and *Inter*)
- **Icons**: Clean inline SVG icons (no heavy external icon libraries)

---

## 🚀 Quick Start Guide

### 1. Clone or Open the Project
Open terminal / command prompt in the project root directory:
```bash
cd cinebook
```

### 2. Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Or install directly: `pip install django Pillow python-dotenv`)*

### 3. Configure Environment Variables
Create your local `.env` configuration file from the provided `.env.example`:
```bash
# On Linux / macOS / PowerShell:
cp .env.example .env

# On Windows Command Prompt:
copy .env.example .env
```

Your `.env` file contains:
- `DJANGO_SECRET_KEY`: A unique, cryptographically strong secret key (never commit this file to Git!).
- `DJANGO_DEBUG`: Set to `True` for local development, `False` in production.
- `DJANGO_ALLOWED_HOSTS`: Comma-separated hosts (`127.0.0.1,localhost`).

To generate a new production secret key at any time:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Run Database Migrations
Create the database tables and constraints:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Load Sample Data (Theatres, Movies, Shows & Test Users)
We have provided a custom management command that populates realistic theatres, screens, 960+ seats, blockbuster movies (*Dune: Part Two*, *Oppenheimer*, *Interstellar*, *The Dark Knight*, etc.), 200+ showtimes, and sample bookings:
```bash
python manage.py seed_data
```

### 6. Run the Automated Tests
Verify booking logic, double-booking prevention, authorization, seat allocation, and page rendering:
```bash
python manage.py test
```
*Expected result: `Ran 8 tests ... OK`*

### 7. Start the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open your browser and visit: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Demo Customer** | `demouser` | `demo1234` | Browse, select seats, book tickets, and view pre-populated bookings. |
| **Superuser / Admin** | `admin` | `admin1234` | Access Django Admin at `/admin/` to manage cinema schedules. |

*You can also register a new account at any time using the "Register" button in the navigation bar.*

---

## 📁 Project Directory Structure

```
cinebook/
├── manage.py                          # Django CLI entry point
├── requirements.txt                   # Project dependencies (Django, Pillow, python-dotenv)
├── .env.example                       # Environment template with placeholders (tracked in Git)
├── .env                               # Local secrets & environment config (EXCLUDED by .gitignore)
├── .gitignore                         # Git exclusion rules (ignores .env, db.sqlite3, media, logs)
├── db.sqlite3                         # SQLite database file (EXCLUDED by .gitignore)
├── README.md                          # Project documentation & deployment guide
├── cinebook/                          # Project configuration package
│   ├── __init__.py
│   ├── settings.py                    # Twelve-Factor environment configuration
│   ├── urls.py                        # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── bookings/                          # Core application
│   ├── __init__.py
│   ├── models.py                      # Movie, Theatre, Screen, Seat, Show, Booking, BookedSeat
│   ├── views.py                       # Home, detail, seats, checkout, confirmation, auth
│   ├── urls.py                        # App route definitions
│   ├── forms.py                       # Registration, Login, and Checkout forms
│   ├── admin.py                       # Admin model registrations & custom displays
│   ├── tests.py                       # Automated test suite (8 tests)
│   └── management/
│       └── commands/
│           ├── __init__.py
│           └── seed_data.py           # Database seeder command
├── static/                            # Static assets
│   ├── css/
│   │   └── main.css                   # Dark theme design system & responsive styles
│   └── js/
│       ├── main.js                    # UI interactions, alert dismissal, trailer modal
│       └── seat_selection.js          # Interactive cinema seat map & price calculation
└── templates/                         # HTML Templates
    ├── base.html                      # Base layout with navbar, search, alerts, footer
    └── bookings/
        ├── home.html                  # Catalog homepage with hero carousel & filters
        ├── movie_detail.html          # Synopsis, cast, date selector, theatre showtimes
        ├── seat_selection.html        # Interactive seat map & live booking summary
        ├── checkout.html              # Contact form, price summary & mock payment
        ├── booking_confirmation.html  # Digital e-ticket with SVG QR code & print
        ├── my_bookings.html           # User booking history & cancellation
        ├── theatres_list.html         # Directory of cinemas, screens & amenities
        ├── auth_login.html            # Sign-in page with demo credentials
        └── auth_register.html         # User sign-up page
```

---

## 🔒 Concurrency, Security & Production Database Considerations

### 1. How CineBook Prevents Double-Booking
When multiple users attempt to reserve the same seats simultaneously:
1. The `confirm_booking` view initiates a database atomic transaction (`transaction.atomic()`).
2. It queries for any existing confirmed booking on the requested seats for that specific show.
3. If an existing booking is detected, the transaction aborts and cleanly notifies the user.
4. Furthermore, the `BookedSeat` model enforces a database-level unique constraint:
   ```python
   class Meta:
       unique_together = ('show', 'seat')
   ```
   Even if two requests pass the application-level check concurrently, the database constraint rejects the second write with an `IntegrityError`, preserving data integrity.

### 2. SQLite vs Production Database (PostgreSQL / MySQL)
- **In Development (SQLite)**: SQLite uses coarse database-level file locks. While perfectly suitable for local development, beginner learning, and low concurrency, SQLite can experience lock contention (`database is locked`) under high concurrent write loads.
- **In Production (PostgreSQL recommended)**:
  - Configure PostgreSQL as the backend in `settings.py`.
  - In PostgreSQL, Django's `.select_for_update()` utilizes row-level locking (`SELECT ... FOR UPDATE`), which locks only the specific seat/show rows during checkout without blocking other shows or users.
  - Connection pooling (e.g. `django-db-geventpool` or PgBouncer) should be employed to handle high peak traffic during major blockbuster ticket drops.

### 3. Server-Side Price Verification
The client only transmits the seat IDs (`seat_ids`). The server:
- Fetches the `Show` and corresponding `Seat` objects from the database.
- Inspects each seat's tier (`VIP`, `PREMIUM`, `STANDARD`).
- Resolves the exact tier price from `show.get_seat_price(seat)`.
- Calculates convenience fees and total amount on the server.
*Any client-side modification of prices or totals in DevTools is completely ignored.*

---

## 🧪 Running Tests

To run the automated test suite:
```bash
python manage.py test bookings
```
The test suite validates:
- Seat generation logic and tier distribution (VIP, Premium, Standard).
- Automatic movie slug creation.
- Login enforcement for checkout and booking confirmation.
- End-to-end booking flow and server-side price calculation.
- Concurrency and duplicate seat booking prevention.
- User authorization and ticket isolation (User A cannot view User B's ticket).
- Booking cancellation and automatic seat release.
- Successful template rendering across all views.
