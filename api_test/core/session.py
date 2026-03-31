"""HTTP 会话构建工具。"""

import requests


def build_retry_session(
    pool_connections: int = 100,
    pool_maxsize: int = 100,
    max_retries: int = 3,
) -> requests.Session:
    """构建带连接池和重试策略的 Session。"""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        max_retries=max_retries,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
