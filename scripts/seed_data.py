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
                "title": "Phase 1: Python Basics",
                "order": 1,
                "lessons": [
                    {"title": "Variables", "order": 1, "content": "Variables in Python."},
                    {"title": "Data Types", "order": 2, "content": "Strings, integers, floats, booleans."},
                    {"title": "Input Output", "order": 3, "content": "Using print() and input()."},
                    {"title": "Operators", "order": 4, "content": "Arithmetic and logical operators."},
                ]
            },
            {
                "title": "Phase 2: Conditions and Loops",
                "order": 2,
                "lessons": [
                    {"title": "If Else", "order": 1, "content": "Conditional statements."},
                    {"title": "Nested Conditions", "order": 2, "content": "If statements inside if statements."},
                    {"title": "For Loop", "order": 3, "content": "Iterating over sequences."},
                    {"title": "While Loop", "order": 4, "content": "Looping until a condition is met."},
                ]
            },
            {
                "title": "Phase 3: Functions",
                "order": 3,
                "lessons": [
                    {"title": "Functions", "order": 1, "content": "Defining reusable blocks of code."},
                    {"title": "Arguments", "order": 2, "content": "Passing data to functions."},
                    {"title": "Lambda", "order": 3, "content": "Anonymous inline functions."},
                    {"title": "Recursion", "order": 4, "content": "Functions calling themselves."},
                ]
            },
            {
                "title": "Phase 4: Data Structures",
                "order": 4,
                "lessons": [
                    {"title": "Lists", "order": 1, "content": "Mutable ordered sequences."},
                    {"title": "Tuples", "order": 2, "content": "Immutable ordered sequences."},
                    {"title": "Sets", "order": 3, "content": "Unordered collections of unique elements."},
                    {"title": "Dictionaries", "order": 4, "content": "Key-value mappings."},
                ]
            },
            {
                "title": "Phase 5: File Handling",
                "order": 5,
                "lessons": [
                    {"title": "Files", "order": 1, "content": "Reading and writing files."},
                    {"title": "Exceptions", "order": 2, "content": "Handling errors using try/except."},
                    {"title": "Modules", "order": 3, "content": "Importing other Python files."},
                ]
            },
            {
                "title": "Phase 6: OOP",
                "order": 6,
                "lessons": [
                    {"title": "Classes", "order": 1, "content": "Defining object blueprints."},
                    {"title": "Objects", "order": 2, "content": "Instantiating classes."},
                    {"title": "Inheritance", "order": 3, "content": "Extending existing classes."},
                    {"title": "Polymorphism", "order": 4, "content": "Using a unified interface."},
                ]
            },
            {
                "title": "Phase 7: Databases",
                "order": 7,
                "lessons": [
                    {"title": "SQLite", "order": 1, "content": "Introduction to SQLite3."},
                    {"title": "CRUD", "order": 2, "content": "Create, Read, Update, Delete."},
                ]
            },
            {
                "title": "Phase 8: APIs",
                "order": 8,
                "lessons": [
                    {"title": "REST APIs", "order": 1, "content": "Understanding RESTful architecture."},
                    {"title": "Requests", "order": 2, "content": "Making HTTP requests in Python."},
                    {"title": "JSON", "order": 3, "content": "Parsing and generating JSON data."},
                ]
            },
            {
                "title": "Phase 9: Web Development",
                "order": 9,
                "lessons": [
                    {"title": "Flask", "order": 1, "content": "Building simple web apps with Flask."},
                    {"title": "FastAPI", "order": 2, "content": "Building high-performance async APIs."},
                ]
            },
            {
                "title": "Phase 10: Job Preparation",
                "order": 10,
                "lessons": [
                    {"title": "Resume", "order": 1, "content": "Crafting a software engineering resume."},
                    {"title": "Projects", "order": 2, "content": "Selecting projects for your portfolio."},
                    {"title": "Interviews", "order": 3, "content": "Preparing for technical interviews."},
                    {"title": "Placements", "order": 4, "content": "Applying to jobs and internships."},
                ]
            }
        ]
    }
]

PROJECTS = [
    {"title": "Calculator", "description": "Build a basic calculator in Python.", "difficulty": "beginner"},
    {"title": "Number Guessing Game", "description": "Create a CLI number guessing game.", "difficulty": "beginner"},
    {"title": "Contact Book", "description": "Store and retrieve contacts using dictionaries.", "difficulty": "beginner"},
    {"title": "Expense Tracker", "description": "Track expenses using file handling or SQLite.", "difficulty": "intermediate"},
    {"title": "Weather App", "description": "Fetch live weather data from an API.", "difficulty": "intermediate"},
    {"title": "Student Management System", "description": "Manage student records using OOP concepts.", "difficulty": "intermediate"},
    {"title": "AI Resume Builder", "description": "Generate dynamic resumes using FastAPI.", "difficulty": "advanced"},
    {"title": "Interview Simulator", "description": "Create an automated interview bot.", "difficulty": "advanced"},
    {"title": "Learning Management System", "description": "Build a comprehensive LMS backend.", "difficulty": "advanced"},
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
