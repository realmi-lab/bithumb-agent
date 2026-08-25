"""TLS verify resolution for httpx/OpenAI provider clients."""

from __future__ import annotations

import logging
import os
import ssl
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def build_system_trust_context() -> ssl.SSLContext:
    """Build a validating SSL context backed by the operating-system roots.

    ``truststore`` reads enterprise roots installed in Windows CryptoAPI,
    macOS Keychain, and Linux's OpenSSL trust paths.  Falling back to certifi
    keeps source checkouts functional before project dependencies are installed.
    """
    try:
        import truststore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except (ImportError, OSError) as exc:
        logger.warning(
            "System trust store is unavailable (%s); using certifi instead",
            exc,
        )
        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()


def _coerce_insecure(ssl_verify: Any) -> bool:
    if ssl_verify is False:
        return True
    if isinstance(ssl_verify, str) and ssl_verify.strip().lower() in {"false", "0", "no", "off"}:
        return True
    return False


def resolve_httpx_verify(
    *,
    ca_bundle: Optional[str] = None,
    ssl_verify: Any = None,
    base_url: str = "",
) -> bool | ssl.SSLContext:
    """Resolve httpx ``verify`` for provider HTTP clients.

    Priority:
    1. ``ssl_verify: false`` — disable verification (local dev only)
    2. explicit ``ca_bundle`` (per-provider ``ssl_ca_cert`` config field)
    3. ``HERMES_CA_BUNDLE``, ``SSL_CERT_FILE``, ``REQUESTS_CA_BUNDLE``,
       ``CURL_CA_BUNDLE`` env vars
    4. the operating-system trust store via ``truststore``

    ``base_url`` is used only for the insecure-mode warning message.
    """
    if _coerce_insecure(ssl_verify):
        logger.warning(
            "TLS certificate verification DISABLED (ssl_verify: false) for %s — "
            "this is intended for local development only and is unsafe on any "
            "network you do not fully control.",
            base_url or "a custom provider endpoint",
        )
        return False

    effective_ca = (
        (ca_bundle or "").strip()
        or os.getenv("HERMES_CA_BUNDLE", "").strip()
        or os.getenv("SSL_CERT_FILE", "").strip()
        or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        or os.getenv("CURL_CA_BUNDLE", "").strip()
    )
    if effective_ca:
        ca_path = str(Path(effective_ca).expanduser())
        if os.path.isfile(ca_path):
            context = build_system_trust_context()
            # Add the explicit enterprise CA without discarding OS roots.
            context.load_verify_locations(cafile=ca_path)
            return context
        logger.warning(
            "CA bundle path does not exist: %s — falling back to default certificates",
            effective_ca,
        )
    return build_system_trust_context()
