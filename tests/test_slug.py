from typing import assert_type

from spend.slug import Slug, slug_like_prefix, to_slug


def test_lowercase():
    slug = "milk"
    assert to_slug(slug) == "milk"


def test_uppercase():
    slug = "MILK"
    assert to_slug(slug) == "milk"


def test_mixed_case():
    slug = "mIlK"
    assert to_slug(slug) == "milk"


def test_idempotent():
    s = to_slug("ACME")
    assert to_slug(s) == s


def test_type():
    slug = "milk"
    # verified by mypy; no-op at runtime
    assert_type(to_slug(slug), Slug)


def test_like_prefix_appends_wildcard():
    assert slug_like_prefix("va") == "va%"


def test_like_prefix_lowercases():
    assert slug_like_prefix("VA") == "va%"


def test_like_prefix_escapes_wildcards():
    # LIKE metacharacters in the prefix must be matched literally.
    assert slug_like_prefix("50%") == "50\\%%"
    assert slug_like_prefix("a_b") == "a\\_b%"
    assert slug_like_prefix("a\\b") == "a\\\\b%"
