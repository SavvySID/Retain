"""Check deployment configuration and refuse to serve an unavailable model."""

from unittest.mock import Mock

import pytest
from flask import Flask

import serve


def test_loopback_default_and_platform_port() -> None:
    """Local serving stays private unless a host is deliberately configured."""
    assert serve.server_settings({}) == ("127.0.0.1", 5050)
    assert serve.server_settings({"HOST": "0.0.0.0", "PORT": "8080"}) == ("0.0.0.0", 8080)
    assert serve.server_settings({"HOST": "localhost", "PORT": "65535"}) == ("localhost", 65535)


@pytest.mark.parametrize("environment", [
    {"PORT": "0"}, {"PORT": "65536"}, {"PORT": "not-a-number"}, {"PORT": ""},
    {"HOST": ""}, {"HOST": "http://127.0.0.1"}, {"HOST": "127.0.0.1:5050"},
])
def test_bad_bind_configuration_is_rejected(environment: dict[str, str]) -> None:
    """Invalid settings fail before attempting a socket bind."""
    with pytest.raises(ValueError):
        serve.server_settings(environment)


def test_unavailable_model_prevents_server_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """A running HTTP process must not masquerade as a ready deployment."""
    application = Flask(__name__)
    application.extensions["churn_service"] = None
    listener = Mock()
    monkeypatch.setattr(serve, "create_app", lambda: application)
    monkeypatch.setattr(serve, "waitress_serve", listener)
    with pytest.raises(RuntimeError, match="Model unavailable"):
        serve.main({})
    listener.assert_not_called()


def test_ready_app_reuses_factory_and_configures_waitress(monkeypatch: pytest.MonkeyPatch) -> None:
    """The deployment path serves the existing application, with bounded requests."""
    application = Flask(__name__)
    application.extensions["churn_service"] = object()
    listener = Mock()
    monkeypatch.setattr(serve, "create_app", lambda: application)
    monkeypatch.setattr(serve, "waitress_serve", listener)
    serve.main({"HOST": "127.0.0.1", "PORT": "5057"})
    listener.assert_called_once()
    assert listener.call_args.args == (application,)
    assert listener.call_args.kwargs["host"] == "127.0.0.1"
    assert listener.call_args.kwargs["port"] == 5057
    assert listener.call_args.kwargs["max_request_body_size"] == 2 * 1024 * 1024 + 65536
    assert listener.call_args.kwargs["inbuf_overflow"] == listener.call_args.kwargs["max_request_body_size"]
