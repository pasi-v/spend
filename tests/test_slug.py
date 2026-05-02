from typing import assert_type

from spend.slug import Slug, to_slug


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
