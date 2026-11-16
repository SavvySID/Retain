"""Serve the trained application locally or on a configured deployment port."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping

from waitress import serve as waitress_serve

from app import MAX_UPLOAD, create_app


def server_settings(environment: Mapping[str, str] | None = None) -> tuple[str, int]:
    """Read a valid bind address/port; default to private localhost."""
    environment = os.environ if environment is None else environment
    host = environment.get("HOST", "127.0.0.1").strip()
    if host != "localhost":
        try:
            ipaddress.ip_address(host)
        except ValueError as error:
            raise ValueError("HOST must be an IP address or localhost, without a scheme or port.") from error
    try:
        port = int(environment.get("PORT", "5050"))
    except ValueError as error:
        raise ValueError("PORT must be an integer between 1 and 65535.") from error
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535.")
    return host, port


def main(environment: Mapping[str, str] | None = None) -> None:
    """Start Waitress only after the existing application loaded a valid model."""
    host, port = server_settings(environment)
    application = create_app()
    if application.extensions.get("churn_service") is None:
        raise RuntimeError("Model unavailable. Run uv run python scripts/train.py before starting the server.")
    print(f"Retain listening on {host}:{port}", flush=True)
    request_limit = MAX_UPLOAD + 65536
    waitress_serve(
        application, host=host, port=port, threads=4,
        max_request_body_size=request_limit,
        # Waitress buffers requests too; keep permitted uploads in RAM before Flask sees them.
        inbuf_overflow=request_limit,
    )


if __name__ == "__main__":
    main()
