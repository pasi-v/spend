from typing import NewType

Slug = NewType("Slug", str)


def to_slug(s: str) -> Slug:
    """the only sanctioned constructor for Slug"""
    return Slug(s.lower())
