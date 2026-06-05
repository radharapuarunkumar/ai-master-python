# AI Master Python

> AI-powered Python learning platform with adaptive tutoring, real-time voice sessions, and comprehensive course management.

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **AI-Powered Tutoring** — Adaptive explanations and quiz generation via Google Gemini
- **Real-Time Voice Sessions** — Live voice/video tutoring powered by LiveKit
- **Course Management** — Structured courses → modules → lessons hierarchy
- **Progress Tracking** — Per-student analytics and learning path recommendations
- **PDF Certificates** — Auto-generated completion certificates with WeasyPrint
- **Async Architecture** — Built on FastAPI + async SQLAlchemy for high concurrency
- **Vector Search** — Semantic similarity search with pgvector embeddings

---

## 🛠 Tech Stack

| Layer           | Technology                            |
| --------------- | ------------------------------------- |
| Framework       | FastAPI 0.115+                        |
| Language        | Python 3.12+                          |
| Database        | PostgreSQL 16 + pgvector              |
| ORM             | SQLAlchemy 2.0 (async)                |
| Migrations      | Alembic                               |
| Cache / Broker  | Redis 7                               |
| Task Queue      | Celery 5.4                            |
| AI              | Google Gemini (google-genai)           |
| Real-Time       | LiveKit                               |
| Auth            | Google OAuth 2.0 + JWT                |
| Storage         | S3-compatible (AWS S3 / MinIO / R2)   |
| Containerization| Docker + Docker Compose               |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2+
- [Python 3.12+](https://python.org) (for local development)
- [GNU Make](https://www.gnu.org/software/make/) (optional, for Makefile shortcuts)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/ai-master-python.git
cd ai-master-python
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys and secrets
```

### 3. Start with Docker Compose

**Production mode:**

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

**Development mode** (hot-reload + pgAdmin):

```bash
make dev
# or without Make:
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build
```

### 4. Run migrations & seed data

```bash
make migrate
make seed
```

### 5. Open the app

- **API:** [http://localhost:8000](http://localhost:8000)
- **Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **pgAdmin (dev):** [http://localhost:5050](http://localhost:5050)

---

## 📁 Project Structure

```
ai-master-python/
├── alembic/                 # Database migrations
│   ├── env.py               # Async migration environment
│   ├── script.py.mako       # Migration template
│   └── versions/            # Generated migration files
├── app/                     # Application source code
│   ├── api/                 # API route handlers
│   ├── config.py            # Pydantic settings
│   ├── main.py              # FastAPI app entry point
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   └── worker/              # Celery tasks
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Multi-stage production build
│   ├── docker-compose.yml   # Production services
│   └── docker-compose.dev.yml  # Dev overrides
├── scripts/                 # Utility scripts
│   └── seed_data.py         # Database seeding
├── tests/                   # Test suite
├── .env.example             # Environment variable template
├── alembic.ini              # Alembic configuration
├── Makefile                 # Developer shortcuts
├── pyproject.toml           # Project metadata & dependencies
└── README.md                # This file
```

---

## 🔧 Development Workflow

### Database Migrations

```bash
# Create a new migration after changing models
make migration m="add enrollment table"

# Apply pending migrations
make migrate

# Roll back one step
make downgrade
```

### Testing

```bash
# Run full test suite with coverage
make test

# Run specific tests
pytest tests/test_courses.py -v

# Run only fast unit tests (skip integration)
pytest -m "not integration"
```

### Linting & Formatting

```bash
# Check for issues (no changes)
make lint

# Auto-fix and format
make format

# Type checking
make typecheck
```

### Security Audit

```bash
make audit
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ by the AI Master Team
</p>
