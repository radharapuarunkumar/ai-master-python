from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/community", tags=["Community"])

class LeaderboardUser(BaseModel):
    id: str
    name: str
    xp: int
    rank: int

class DiscussionPost(BaseModel):
    id: str
    author: str
    content: str
    likes: int
    time_ago: str

# Sample Data
SAMPLE_LEADERBOARD = [
    LeaderboardUser(id="1", name="Arun Kumar", xp=1500, rank=1),
    LeaderboardUser(id="2", name="Priya Singh", xp=1200, rank=2),
    LeaderboardUser(id="3", name="Rahul Dev", xp=950, rank=3),
]

SAMPLE_POSTS = [
    DiscussionPost(id="p1", author="Arun Kumar", content="Just finished the Python Basics phase! The quiz on Data Types was tricky.", likes=5, time_ago="2 hours ago"),
    DiscussionPost(id="p2", author="Priya Singh", content="Can someone explain how decorators work? I'm stuck.", likes=2, time_ago="4 hours ago"),
]

@router.get("/leaderboard", response_model=ResponseEnvelope[List[LeaderboardUser]])
async def get_leaderboard():
    """Get XP leaderboard."""
    return ResponseEnvelope(data=SAMPLE_LEADERBOARD)

@router.get("/feed", response_model=ResponseEnvelope[List[DiscussionPost]])
async def get_feed():
    """Get discussion feed."""
    return ResponseEnvelope(data=SAMPLE_POSTS)
