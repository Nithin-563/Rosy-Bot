"""Database URL normalization.

Railway's ``POSTGRES_URL`` is ``postgresql://user:pass@host:port/db`` — a
*sync* psycopg2 URL. Rosy uses SQLAlchemy async, which needs the ``+asyncpg``
driver. This helper rewrites plain ``postgresql://`` / ``postgres://`` URLs to
``postgresql+asyncpg://`` so the app and Alembic both work whether the user
provides a sync or async URL.
"""

from urllib.parse import urlsplit, urlunsplit


def normalize_database_url(url: str | None) -> str:
    """Return a URL that SQLAlchemy async can use."""
    if not url:
        return url  # caller falls back to default
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme in ("postgresql", "postgres") and "+" not in scheme:
        # Rewrite to the asyncpg driver.
        scheme = "postgresql+asyncpg"
        return urlunsplit((scheme,) + parts[1:])
    return url
