# Meal Planet

A self-hosted meal planning and grocery management app that automates recipe importing, weekly meal scheduling, smart grocery aggregation, and budget estimation — all powered by LLM-driven intelligence.

Built for a single family. No accounts, no sign-ups. Just deploy with Docker and start planning.

> **New to this?** If you've never used Docker or a terminal before, follow the [step-by-step instructions for non-technical users](INSTRUCTIONS.md).

## Features

- **Recipe Management** — Create, edit, and browse recipes with ingredients, instructions, tags, and category (breakfast, lunch, dinner, dessert, any).
- **LLM-Powered Recipe Import** — Paste a URL and Gemini 2.5 Flash extracts a fully structured recipe (ingredients, quantities, units, instructions, tags, category) automatically. At least 3 tags are extracted per recipe.
- **Weekly Meal Planner** — Assign recipes to a calendar by date and type (breakfast, lunch, dinner). Set serving sizes per meal.
- **Fill Week** — One-click auto-fill for empty meal slots using category-matched recipes and weighted random selection.
- **Smart Grocery List** — Generates a deduplicated, category-sorted grocery list across all planned meals with unit conversion and intelligent rounding to realistic package sizes. Lists are persisted and can be viewed from an archive.
- **Walmart Price Estimation** — Gemini estimates prices for each ingredient mapped to Walmart products. Results are cached for 7 days.
- **Dinner Spinner** — A weighted random recipe picker that favors meals you haven't cooked recently. Filter by tags.
- **Reports Dashboard** — Spending over time, top 5 most-used recipes, most expensive day, and average spending by grocery category.
- **iCalendar Export** — Export your meal plan as an `.ics` file for Google Calendar, Outlook, or Apple Calendar.
- **Tag Editing** — Add, remove, and edit tags directly on any recipe detail page.

## Tech Stack

| Layer      | Technology                                                |
| ---------- | --------------------------------------------------------- |
| Frontend   | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| Backend    | FastAPI, Python 3.12, Uvicorn                             |
| Database   | PostgreSQL 16                                             |
| Task Queue | Dramatiq + Redis 7                                        |
| LLM        | Google Gemini 2.5 Flash                                   |
| Scraping   | Playwright (headless)                                     |
| Deployment | Docker Compose                                            |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               Frontend (Next.js :3000)                │
│  Dashboard · Planner · Recipes · Spinner · Grocery    │
│  Reports                                              │
└────────────────────────┬─────────────────────────────┘
                         │ REST
┌────────────────────────┴─────────────────────────────┐
│               Backend (FastAPI :8000)                  │
│   /api/recipes · /api/meal-plan · /api/grocery-list   │
│   /api/spinner · /api/calendar · /api/reports         │
└───────┬──────────────────────────────────┬───────────┘
        │                                  │
        ▼                                  ▼
┌───────────────┐              ┌────────────────────┐
│  PostgreSQL   │              │  Redis + Dramatiq  │
│  (data store) │              │  (task queue)      │
└───────────────┘              └────────┬───────────┘
                                        │
                                        ▼
                               ┌────────────────────┐
                               │  Worker Service     │
                               │  · Recipe parsing   │
                               │  · Price estimation  │
                               │  · Gemini API calls  │
                               └────────────────────┘
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [Google Gemini API key](https://ai.google.dev/)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/geraldfingburke/meal-planet.git
   cd meal-planet
   ```

2. **Create a `.env` file** in the project root:

   ```env
   POSTGRES_USER=mealplanet
   POSTGRES_PASSWORD=changeme
   POSTGRES_DB=mealplanet
   DATABASE_URL=postgresql+asyncpg://mealplanet:changeme@db:5432/mealplanet
   REDIS_URL=redis://redis:6379/0
   BACKEND_CORS_ORIGINS=http://localhost:3000
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=change-this-in-production
   ```

3. **Start all services**

   ```bash
   docker compose up --build
   ```

4. **Seed the database**

   ```bash
   docker compose exec backend python -m app.seed
   ```

   This creates the default family record and common ingredients.

5. **Open the app** at [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method   | Path                                    | Description                                 |
| -------- | --------------------------------------- | ------------------------------------------- |
| `GET`    | `/health`                               | Health check                                |
| `GET`    | `/api/recipes`                          | List recipes (query: `q`, `tag`)            |
| `GET`    | `/api/recipes/{id}`                     | Get recipe details                          |
| `POST`   | `/api/recipes`                          | Create recipe (with category + tags)        |
| `PUT`    | `/api/recipes/{id}`                     | Update recipe (title, tags, category, etc.) |
| `DELETE` | `/api/recipes/{id}`                     | Delete recipe                               |
| `POST`   | `/api/recipes/import`                   | Import recipe from URL (async)              |
| `GET`    | `/api/ingredients`                      | List ingredients (query: `q`, `category`)   |
| `POST`   | `/api/ingredients`                      | Create ingredient                           |
| `GET`    | `/api/meal-plan`                        | List meal plan (query: `week_start`)        |
| `POST`   | `/api/meal-plan`                        | Create meal plan entry (with servings)      |
| `PUT`    | `/api/meal-plan/{id}`                   | Update meal plan entry                      |
| `DELETE` | `/api/meal-plan/{id}`                   | Delete meal plan entry                      |
| `POST`   | `/api/meal-plan/fill-week`              | Auto-fill empty slots with matched recipes  |
| `POST`   | `/api/grocery-list/generate`            | Generate aggregated grocery list            |
| `GET`    | `/api/grocery-list/latest`              | Get most recent generated list              |
| `GET`    | `/api/grocery-list/archives`            | List all saved grocery lists                |
| `GET`    | `/api/grocery-list/archives/{id}`       | Get a specific archived list                |
| `GET`    | `/api/spinner/spin`                     | Random weighted recipe (query: `tags`)      |
| `GET`    | `/api/spinner/tags`                     | List available tags                         |
| `GET`    | `/api/calendar/export.ics`              | Export iCal (query: `start`, `end`)         |
| `GET`    | `/api/jobs/{id}`                        | Check background job status                 |
| `GET`    | `/api/reports/spending-over-time`       | Grocery spending history                    |
| `GET`    | `/api/reports/top-recipes`              | Top 5 most-used recipes                     |
| `GET`    | `/api/reports/most-expensive-day`       | Highest-cost meal day                       |
| `GET`    | `/api/reports/avg-spending-by-category` | Average spending per grocery category       |

## How It Works

### Serving Size Scaling

Each recipe stores a base serving count. Serving sizes are configured per meal on the planner. When generating grocery lists, quantities scale from the recipe base to the meal's serving count:

$$Q_{calc} = Q_{base} \times \frac{S_{meal}}{S_{base}}$$

### Dinner Spinner Weights

The spinner avoids recently cooked meals using a weighted random selection:

| Last Cooked            | Weight |
| ---------------------- | ------ |
| Never or > 14 days ago | 3×     |
| 7–14 days ago          | 2×     |
| < 7 days ago           | 1×     |

### Recipe Import Pipeline

1. User submits a URL
2. Backend creates an async job and returns a job ID
3. Dramatiq worker fetches the page HTML
4. Gemini extracts structured recipe data (ingredients, quantities, units, instructions)
5. Recipe is saved to the database
6. Price estimation is triggered for new ingredients

## Project Structure

```
meal-planet/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + router mounting
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # Async SQLAlchemy setup
│   │   ├── seed.py            # Database seeding
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routers/           # API route handlers
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Dramatiq background tasks
│   │   └── utils/             # Unit conversion helpers
│   └── alembic/               # Database migrations
├── frontend/
│   └── src/
│       ├── app/               # Next.js pages
│       ├── components/        # React components
│       └── lib/               # API client + utilities
└── scripts/
    └── init-db.sql            # Database initialization
```

## License

This project is released under [The Unlicense](LICENSE) — public domain. Do whatever you want with it.
