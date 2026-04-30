# TiffinTrack

TiffinTrack is a Django-based tiffin/mess subscription platform where users can discover nearby mess providers, subscribe to daily meal plans, and manage deliveries from one place.

## What The Project Is

TiffinTrack supports three roles:
- `Users`: browse nearby restaurants/mess providers, subscribe to menu plans, track orders, cancel eligible meals, manage addresses, and raise order/restaurant reports.
- `Restaurant owners`: register their restaurant, manage menu categories and food items, handle subscriptions/orders, and run offers.
- `Admins`: review and manage users/restaurants, monitor platform orders and revenue, and handle complaints/reporting.

## Core Features

- Location-aware restaurant discovery using GeoDjango/PostGIS
- Monthly/daily-style subscription flow for meal plans
- Menu management (menu categories, food categories, day-wise food items)
- Order lifecycle with cancellation and wallet refund handling
- Wallet and transaction tracking
- Coupon, referral, and offer support
- Razorpay payment integration
- OTP/password flows and Google social login (`django-allauth`)
- Cloudinary media storage for uploaded images

## Tech Stack

- Python + Django 5
- PostgreSQL + PostGIS
- GeoDjango
- Razorpay, Twilio, WeasyPrint, Cloudinary
- Docker / Docker Compose

## Project Apps

- `accounts`: authentication, profiles, role handling, OTP/email flows
- `users`: user-facing discovery, subscriptions, orders, wallet, reporting
- `restaurant`: restaurant dashboard, menu/offer/subscription management
- `admin_panel`: admin dashboard, moderation, analytics, exports
- `payments`: Razorpay payment flow
- `coupons`: coupons, usage tracking, referrals

## Docker Setup

### 1) Prepare environment variables

Keep a root `.env` file (next to `docker-compose.yml`) with your project variables.
Docker compose sets `DB_HOST=postgres` and `DB_PORT=5432` automatically for the Django container.

### 2) Build and run

```bash
docker compose up --build
```

This will:
- start PostgreSQL (PostGIS) and Django containers
- run migrations
- start Django on port `8000`

Open: `http://localhost:8000`

### 3) Stop services

```bash
docker compose down
```

To remove volumes too:

```bash
docker compose down -v
```
