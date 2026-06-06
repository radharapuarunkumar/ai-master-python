"""Seed script — populates the database with initial sample data.

Usage:
    python scripts/seed_data.py

This script is idempotent: it checks for existing records before inserting
and can be re-run safely without creating duplicates.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ensure the project root is on sys.path so we can import `app`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.base import Base

# ---------------------------------------------------------------------------
# We import the models lazily so this script works even when the full app
# hasn't been installed yet.  Adjust these imports to match your actual
# model locations once they are created.
# ---------------------------------------------------------------------------
try:
    from app.models.project import Project
    from app.models.resume import Resume
    from app.models.certificate import Certificate
except ImportError:
    print(
        "WARNING: Some model modules could not be imported.\n"
        "This is expected if the models have not been created yet.\n"
        "Please create the model files and re-run this script.\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Sample data definitions
# ---------------------------------------------------------------------------
ADMIN_USER = {
    "email": "admin@aimaster.dev",
    "full_name": "Admin User",
    "role": "admin",
    "is_active": True,
}

ARUN_USER = {
    "email": "arun@aimaster.dev",
    "full_name": "Arun Kumar",
    "role": "free",
    "is_active": True,
}

COURSES = [
    {
        "title": "Python Basics",
        "description": "Learn the fundamentals of Python programming from scratch.",
        "difficulty": "beginner",
        "modules": [
            {
                "title": "Getting Started with Python",
                "order": 1,
                "lessons": [
                    {"title": "Installing Python", "order": 1, "content": "How to install Python on your system."},
                    {"title": "Your First Program", "order": 2, "content": "Writing and running your first Python script."},
                    {"title": "Variables and Data Types", "order": 3, "content": "Understanding variables, strings, numbers, and booleans."},
                ],
            },
        ],
    },
]

PROJECTS = [
    {"title": "Terminal To-Do List", "description": "Build a CLI to-do app using Python.", "difficulty": "beginner"},
    {"title": "Weather API Fetcher", "description": "Use requests to fetch weather data.", "difficulty": "beginner"},
    {"title": "Web Scraper", "description": "Scrape a website using BeautifulSoup.", "difficulty": "intermediate"},
    {"title": "Flask API", "description": "Build a basic REST API with Flask.", "difficulty": "intermediate"},
    {"title": "Discord Bot", "description": "Create a Discord bot with discord.py.", "difficulty": "advanced"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def record_exists(session: AsyncSession, model, **filters) -> bool:  # noqa: ANN001
    """Return True if a record matching the filters already exists."""
    stmt = select(model).filter_by(**filters)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------
async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # --- Users ---
            if not await record_exists(session, User, email=ADMIN_USER["email"]):
                admin = User(id=uuid4(), **ADMIN_USER)
                session.add(admin)
                print(f"✓ Created admin user: {ADMIN_USER['email']}")
            
            arun_id = uuid4()
            if not await record_exists(session, User, email=ARUN_USER["email"]):
                arun = User(id=arun_id, **ARUN_USER)
                session.add(arun)
                print(f"✓ Created user: {ARUN_USER['email']}")
            else:
                stmt = select(User).where(User.email == ARUN_USER['email'])
                res = await session.execute(stmt)
                arun_id = res.scalar_one().id

            # --- Projects ---
            for proj in PROJECTS:
                if not await record_exists(session, Project, title=proj["title"]):
                    p = Project(id=uuid4(), title=proj["title"], description=proj["description"], difficulty=proj["difficulty"])
                    session.add(p)
            print("✓ Seeded projects")

            # --- Resume ---
            if not await record_exists(session, Resume, user_id=arun_id):
                resume = Resume(
                    id=uuid4(),
                    user_id=arun_id,
                    title="Python Backend Developer",
                    target_job_title="Software Engineer",
                    content={"experience": "1 year Python"}
                )
                session.add(resume)
            print("✓ Seeded resume")

            # --- Certificate ---
            if not await record_exists(session, Certificate, user_id=arun_id):
                cert = Certificate(
                    id=uuid4(),
                    user_id=arun_id,
                    course_id=uuid4(), # dummy course id
                    certificate_number="CERT-ARUN-123",
                    verification_hash="hash123"
                )
                session.add(cert)
            print("✓ Seeded certificate")

    await engine.dispose()
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
