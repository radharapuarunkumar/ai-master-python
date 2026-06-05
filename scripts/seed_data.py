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
    from app.models.user import User
    from app.models.course import Course
    from app.models.module import Module
    from app.models.lesson import Lesson
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
            {
                "title": "Control Flow",
                "order": 2,
                "lessons": [
                    {"title": "If Statements", "order": 1, "content": "Making decisions with if, elif, and else."},
                    {"title": "Loops", "order": 2, "content": "Repeating code with for and while loops."},
                ],
            },
        ],
    },
    {
        "title": "Intermediate Python",
        "description": "Level up with functions, OOP, and file handling.",
        "difficulty": "intermediate",
        "modules": [
            {
                "title": "Functions & Modules",
                "order": 1,
                "lessons": [
                    {"title": "Defining Functions", "order": 1, "content": "Creating reusable code with def."},
                    {"title": "Modules and Imports", "order": 2, "content": "Organizing code across files."},
                ],
            },
            {
                "title": "Object-Oriented Programming",
                "order": 2,
                "lessons": [
                    {"title": "Classes and Objects", "order": 1, "content": "Introduction to OOP concepts."},
                    {"title": "Inheritance", "order": 2, "content": "Reusing and extending classes."},
                    {"title": "Magic Methods", "order": 3, "content": "Customizing class behavior with dunder methods."},
                ],
            },
            {
                "title": "File I/O & Error Handling",
                "order": 3,
                "lessons": [
                    {"title": "Reading and Writing Files", "order": 1, "content": "Working with text and binary files."},
                    {"title": "Exception Handling", "order": 2, "content": "Gracefully handling errors with try/except."},
                ],
            },
        ],
    },
    {
        "title": "Advanced Python",
        "description": "Master async programming, metaprogramming, and performance.",
        "difficulty": "advanced",
        "modules": [
            {
                "title": "Async Programming",
                "order": 1,
                "lessons": [
                    {"title": "Coroutines and async/await", "order": 1, "content": "Understanding the async execution model."},
                    {"title": "asyncio in Practice", "order": 2, "content": "Building concurrent applications with asyncio."},
                ],
            },
            {
                "title": "Metaprogramming",
                "order": 2,
                "lessons": [
                    {"title": "Decorators Deep Dive", "order": 1, "content": "Advanced decorator patterns and use cases."},
                    {"title": "Metaclasses", "order": 2, "content": "Controlling class creation with metaclasses."},
                    {"title": "Descriptors", "order": 3, "content": "Understanding the descriptor protocol."},
                ],
            },
        ],
    },
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
            # --- Admin user ---
            if not await record_exists(session, User, email=ADMIN_USER["email"]):
                admin = User(id=str(uuid4()), **ADMIN_USER)
                session.add(admin)
                print(f"✓ Created admin user: {ADMIN_USER['email']}")
            else:
                print(f"· Admin user already exists: {ADMIN_USER['email']}")

            # --- Courses, modules, lessons ---
            for course_data in COURSES:
                if await record_exists(session, Course, title=course_data["title"]):
                    print(f"· Course already exists: {course_data['title']}")
                    continue

                course = Course(
                    id=str(uuid4()),
                    title=course_data["title"],
                    description=course_data["description"],
                    difficulty=course_data["difficulty"],
                    is_published=True,
                )
                session.add(course)
                # Flush to get the course ID before creating children
                await session.flush()

                for mod_data in course_data["modules"]:
                    module = Module(
                        id=str(uuid4()),
                        course_id=course.id,
                        title=mod_data["title"],
                        order=mod_data["order"],
                    )
                    session.add(module)
                    await session.flush()

                    for lesson_data in mod_data["lessons"]:
                        lesson = Lesson(
                            id=str(uuid4()),
                            module_id=module.id,
                            title=lesson_data["title"],
                            content=lesson_data["content"],
                            order=lesson_data["order"],
                        )
                        session.add(lesson)

                print(f"✓ Created course: {course_data['title']} "
                      f"({len(course_data['modules'])} modules)")

    await engine.dispose()
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
