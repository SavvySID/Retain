"""Pin the requested home-page structure without duplicating its styling."""

from html.parser import HTMLParser

import pytest
from flask.testing import FlaskClient

from app import create_app


class HomeStructure(HTMLParser):
    """Count native landmarks and FAQ controls in the server-rendered document."""

    def __init__(self) -> None:
        super().__init__()
        self.headings = 0
        self.details = 0
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.headings += tag == "h1"
        self.details += tag == "details"
        if attributes.get("id"):
            self.ids.add(attributes["id"])


@pytest.fixture(scope="module")
def client() -> FlaskClient:
    """Use the same application factory and real local model as the website."""
    return create_app().test_client()


def test_home_has_single_hero_real_preview_and_native_faq(client: FlaskClient) -> None:
    parser = HomeStructure()
    parser.feed(client.get("/").get_data(as_text=True))
    assert parser.headings == 1
    assert parser.details >= 3
    assert {"home-hero", "home-faq", "home-cohort-chart", "home-factors"} <= parser.ids


def test_product_pages_keep_the_existing_model_and_privacy_contract(client: FlaskClient) -> None:
    for path in ("/", "/overview", "/analysis", "/batch", "/models", "/guide"):
        response = client.get(path)
        assert response.status_code == 200
        assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/api/schema").json["excluded_features"] == [
        "customerID", "Churn", "gender", "SeniorCitizen"
    ]
