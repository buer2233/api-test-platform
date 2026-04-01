"""HTTP session builder for the generic test runtime."""

from __future__ import annotations

import requests
from urllib3.util import Retry

from core.config_loader import get_api_config


def build_retry_session(
    pool_connections: int | None = None,
    pool_maxsize: int | None = None,
    max_retries: int | None = None,
) -> requests.Session:
    """Build a requests session using JSON configuration defaults."""
    api_config = get_api_config()
    config = api_config.session
    retry_policy = Retry(
        total=max_retries if max_retries is not None else config.max_retries,
        connect=max_retries if max_retries is not None else config.max_retries,
        read=max_retries if max_retries is not None else config.max_retries,
        status=max_retries if max_retries is not None else config.max_retries,
        allowed_methods=None,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=pool_connections if pool_connections is not None else config.pool_connections,
        pool_maxsize=pool_maxsize if pool_maxsize is not None else config.pool_maxsize,
        max_retries=retry_policy,
    )
    session = requests.Session()
    if api_config.proxy.enabled:
        session.proxies.update(
            {
                "http": api_config.proxy.url,
                "https": api_config.proxy.url,
            }
        )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
