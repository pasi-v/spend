from typing import NewType

Slug = NewType("Slug", str)


def to_slug(s: str) -> Slug:
    """the only sanctioned constructor for Slug"""
    return Slug(s.lower())


def slug_like_prefix(prefix: str) -> str:
    """Build an escaped SQL LIKE pattern matching slugs that start with
    `prefix` (case-insensitively, since slugs are stored lowercased).

    Use with ``... WHERE slug LIKE ? ESCAPE '\\'``. The `%` and `_` LIKE
    wildcards (and the escape char itself) are escaped so a prefix
    containing them is matched literally."""
    normalized = to_slug(prefix)
    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "%"
