"""Check routable pages and real held-out cohort analytics."""
import pytest

from app import create_app


@pytest.fixture(scope="module")
def client():
    """Use actual trusted model artifacts."""
    return create_app().test_client()


@pytest.mark.parametrize("path", ["/", "/overview", "/analysis", "/batch", "/models", "/guide"])
def test_pages_are_refreshable(client, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert b"Retain" in response.data


def test_home_is_a_product_page(client) -> None:
    assert b'id="home-hero"' in client.get("/").data
    assert b'href="/overview"' in client.get("/").data


@pytest.mark.parametrize("contract", ["", "Month-to-month", "One year", "Two year"])
def test_cohort_chart_matches_source_rows(client, contract: str) -> None:
    response = client.get("/api/cohorts", query_string={"contract": contract})
    assert response.status_code == 200
    result = response.json
    rows = client.application.extensions["churn_service"].customers
    rows = [row for row in rows if not contract or row["features"]["Contract"] == contract]
    assert result["population"] == "held-out test"
    assert result["count"] == len(rows)
    assert sum(group["count"] for group in result["bins"]) == len(rows)
    for group in result["bins"]:
        members = [row for row in rows if group["min_tenure"] <= row["features"]["tenure"] <= group["max_tenure"]]
        assert group["count"] == len(members)
        if members:
            assert group["churn_rate"] == pytest.approx(sum(r["actual_churn"] for r in members) / len(members))
            assert group["mean_probability"] == pytest.approx(sum(r["probability"] for r in members) / len(members))
        else:
            assert group["churn_rate"] is None and group["mean_probability"] is None


def test_bad_cohort_filter_is_rejected(client) -> None:
    assert client.get("/api/cohorts?contract=unknown").status_code == 400
