# TiffinTrack
Django application to manage mess ( monthly food scheme )

What if there is an application to order food for monthly basis? 

This application will allow you to search for nearby mess services and you can order/canel food from them.

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
