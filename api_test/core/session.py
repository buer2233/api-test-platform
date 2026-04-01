"""HTTP session builder for the generic test runtime."""

from __future__ import annotations

import requests

from core.config_loader import get_api_config


def build_retry_session(
    pool_connections: int | None = None,
    pool_maxsize: int | None = None,
    max_retries: int | None = None,
) -> requests.Session:
    """Build a requests session using JSON configuration defaults."""
    config = get_api_config().session
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=pool_connections if pool_connections is not None else config.pool_connections,
        pool_maxsize=pool_maxsize if pool_maxsize is not None else config.pool_maxsize,
        max_retries=max_retries if max_retries is not None else config.max_retries,
    )
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
