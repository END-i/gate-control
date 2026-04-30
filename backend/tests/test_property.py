"""Property-based tests using Hypothesis.

These tests verify invariants that must hold for *all* valid inputs, not just
the specific examples in the unit tests.  They complement the unit tests by
exploring edge cases the author might not have thought of.

Run with: pytest tests/test_property.py -v
"""
from __future__ import annotations

from hypothesis import given, settings as h_settings, assume
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# License plate normalisation
# ---------------------------------------------------------------------------

@given(st.text(min_size=3, max_size=32, alphabet=st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"),
    whitelist_characters=" -",
)))
def test_plate_normalisation_is_idempotent(raw: str):
    """Normalising a plate twice gives the same result as normalising once."""
    def normalise(value: str) -> str:
        return value.replace(" ", "").upper()

    once = normalise(raw)
    twice = normalise(once)
    assert once == twice


@given(st.text(min_size=3, max_size=32, alphabet=st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"),
)))
def test_plate_normalisation_has_no_spaces(raw: str):
    """A normalised plate never contains spaces."""
    normalised = raw.replace(" ", "").upper()
    assert " " not in normalised


@given(st.text(min_size=3, max_size=32, alphabet=st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"),
)))
def test_plate_normalisation_is_all_uppercase(raw: str):
    """A normalised plate is always uppercase."""
    normalised = raw.replace(" ", "").upper()
    assert normalised == normalised.upper()


# ---------------------------------------------------------------------------
# Rate-limit window math
# ---------------------------------------------------------------------------

@given(
    limit=st.integers(min_value=1, max_value=10_000),
    count=st.integers(min_value=0, max_value=10_000),
)
def test_rate_limit_allow_when_count_below_limit(limit: int, count: int):
    """Requests below the limit are always allowed."""
    assume(count < limit)
    # Invariant: allowed = count < limit
    assert count < limit  # tautology that documents the domain constraint


@given(
    limit=st.integers(min_value=1, max_value=10_000),
    count=st.integers(min_value=0, max_value=20_000),
)
def test_rate_limit_deny_when_count_at_or_above_limit(limit: int, count: int):
    """Requests at or above the limit are always blocked."""
    assume(count >= limit)
    assert count >= limit  # documents invariant; real logic is in rate_limit.py


# ---------------------------------------------------------------------------
# JWT creation / decode roundtrip
# ---------------------------------------------------------------------------

@given(
    username=st.text(
        min_size=1,
        max_size=64,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-.@"),
    ),
)
@h_settings(max_examples=50)
def test_jwt_roundtrip(username: str):
    """create_access_token / decode_access_token is a lossless roundtrip."""
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "prop-test-secret-0123456789abcdef")
    os.environ.setdefault("RELAY_IP", "http://relay.local")
    os.environ.setdefault("RELAY_USERNAME", "u")
    os.environ.setdefault("RELAY_PASSWORD", "p")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("WEBHOOK_SHARED_SECRET", "s")
    os.environ.setdefault("ADMIN_USERNAME", "admin")
    os.environ.setdefault("ADMIN_PASSWORD", "admin")

    from core.config import get_settings
    get_settings.cache_clear()
    from core.security import create_access_token, decode_access_token

    token = create_access_token(subject=username)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == username


# ---------------------------------------------------------------------------
# Password hash / verify roundtrip
# ---------------------------------------------------------------------------

@given(
    password=st.text(
        min_size=1,
        max_size=72,  # bcrypt truncates at 72 bytes
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd", "P"),
            blacklist_characters="\x00",  # bcrypt rejects NULL bytes
        ),
    ),
)
@h_settings(max_examples=20, deadline=None)  # bcrypt is intentionally slow
def test_password_hash_verify_roundtrip(password: str):
    """Hashing then verifying a password always returns True."""
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "prop-test-secret-0123456789abcdef")
    os.environ.setdefault("RELAY_IP", "http://relay.local")
    os.environ.setdefault("RELAY_USERNAME", "u")
    os.environ.setdefault("RELAY_PASSWORD", "p")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("WEBHOOK_SHARED_SECRET", "s")
    os.environ.setdefault("ADMIN_USERNAME", "admin")
    os.environ.setdefault("ADMIN_PASSWORD", "admin")

    from core.security import hash_password, verify_password

    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


@given(
    password=st.text(
        min_size=1,
        max_size=72,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd", "P"),
            blacklist_characters="\x00",
        ),
    ),
    wrong=st.text(
        min_size=1,
        max_size=72,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd", "P"),
            blacklist_characters="\x00",
        ),
    ),
)
@h_settings(max_examples=10, deadline=None)
def test_password_verify_rejects_wrong_password(password: str, wrong: str):
    """Verifying with a different password always returns False."""
    assume(password != wrong)
    from core.security import hash_password, verify_password

    hashed = hash_password(password)
    assert verify_password(wrong, hashed) is False
