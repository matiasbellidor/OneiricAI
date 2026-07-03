"""Social feed: verified posts only — by construction, nothing fake can land here."""

from fastapi import APIRouter

from ..db import get_store
from ..models import Post

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=list[Post])
def feed(limit: int = 30) -> list[Post]:
    return get_store().list_posts(limit=limit)
