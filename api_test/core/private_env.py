"""私有环境依赖治理工具。"""

from __future__ import annotations

import base64
import os

import rsa

from config import RunConfig


PLACEHOLDER_PUBLIC_KEY_FRAGMENT = "..."


class PrivateEnvDependencyError(RuntimeError):
    """私有环境必要依赖缺失。"""


def resolve_rsa_public_key(explicit_key: str | None = None) -> str:
    """获取当前私有环境登录需要的 RSA 公钥。"""
    candidate = explicit_key or os.getenv("API_TEST_RSA_PUBLIC_KEY") or getattr(RunConfig, "RSA_PUBLIC_KEY", "")
    normalized = candidate.strip()
    if not normalized or PLACEHOLDER_PUBLIC_KEY_FRAGMENT in normalized:
        raise PrivateEnvDependencyError("未配置有效 RSA 公钥，请设置 API_TEST_RSA_PUBLIC_KEY。")
    return normalized


def load_rsa_public_key(public_key_pem: str) -> rsa.PublicKey:
    raw_key = public_key_pem.encode("utf-8")
    for loader in (rsa.PublicKey.load_pkcs1_openssl_pem, rsa.PublicKey.load_pkcs1):
        try:
            return loader(raw_key)
        except ValueError:
            continue
    raise PrivateEnvDependencyError("RSA 公钥格式无效，无法用于私有环境登录。")


def encrypt_password(password: str, public_key_pem: str | None = None) -> str:
    """使用显式配置的 RSA 公钥加密密码。"""
    public_key = load_rsa_public_key(resolve_rsa_public_key(public_key_pem))
    encrypted = rsa.encrypt(password.encode("utf-8"), public_key)
    return base64.b64encode(encrypted).decode("utf-8").replace("\n", "")
