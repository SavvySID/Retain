"""Exercise the real local dashboard and save screenshots and check results."""

from __future__ import annotations

import argparse
import csv
import io
import json
from itertools import pairwise
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def assert_no_overflow(page: Page) -> None:
    """Allow card-contained table scrolling, but reject whole-page overflow."""
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), page.evaluate("""({
      viewport:innerWidth, width:document.documentElement.scrollWidth, x:scrollX, view:location.hash,
      elements:[...document.querySelectorAll('body *')].filter(el =>
        el.getBoundingClientRect().right + scrollX > innerWidth + 1).map(el => ({tag:el.tagName, id:el.id,
        cls:el.className, right:el.getBoundingClientRect().right+scrollX,
        overflow:getComputedStyle(el).overflowX})).slice(0,15)})""")


def navigate(page: Page, view: str) -> None:
    """Navigate through the real sidebar, opening the mobile drawer if needed."""
    link = page.locator(f".nav-link[data-view='{view}']")
    # Wait for the breakpoint handler before deciding whether the drawer needs opening.
    page.wait_for_function("""() => {
      const mobile=matchMedia('(max-width:767px)').matches;
      const sidebar=document.querySelector('#sidebar');
      return mobile ? sidebar.inert || document.body.classList.contains('mobile-sidebar-open') : !sidebar.inert;
    }""")
    needs_drawer = page.evaluate("matchMedia('(max-width:767px)').matches && !document.body.classList.contains('mobile-sidebar-open')")
    if needs_drawer:
        page.locator("#sidebar-toggle").click()
    link.click()
    expect(page.locator(f"#view-{view}")).to_be_visible()


def check_dashboard(base_url: str) -> dict[str, Any]:
    """Check actual API data, prediction and export workflows, and responsive layouts."""
    output = ROOT / "artifacts" / "browser"
    output.mkdir(parents=True, exist_ok=True)
    checks: list[str] = []
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
        # Delay real responses for race checks; payloads and metrics are never mocked.
        context.add_init_script("""const originalFetch = window.fetch;
          window.__predictionDelays = [];
          window.__cohortDelays = [];
          window.__failNextCohort = false;
          window.fetch = async (...args) => {
            const url = String(args[0]);
            if (url.includes('/api/cohorts') && window.__failNextCohort) {
              window.__failNextCohort = false;
              throw new Error('Deliberate browser regression transport failure');
            }
            const delay = url.endsWith('/api/predict') ? (window.__predictionDelays.shift() || 0) :
              url.includes('/api/cohorts') ? (window.__cohortDelays.shift() || 0) : 0;
            const response = await originalFetch(...args);
            if (delay) await new Promise(resolve => setTimeout(resolve, delay));
            return response;
          };""")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(f"{base_url}/", wait_until="networkidle")
        expect(page.locator("#home-hero")).to_be_visible()
        assert page.locator("a[href='/overview']").count() > 0
        assert_no_overflow(page)
        page.screenshot(path=str(output / "home-desktop.png"), full_page=True)
        page.goto(f"{base_url}/guide", wait_until="networkidle")
        expect(page.get_by_role("heading", level=1)).to_be_visible()
        assert_no_overflow(page)
        for path in ("overview", "analysis", "batch", "models"):
            page.goto(f"{base_url}/{path}", wait_until="networkidle")
            expect(page.locator(f"#view-{path}")).to_be_visible()
            page.reload(wait_until="networkidle")
            expect(page.locator(f"#view-{path}")).to_be_visible()
        checks.append("home, guide and workspace routes support direct entry and refresh")
        page.goto(f"{base_url}/#analysis")
        page.wait_for_url("**/analysis")
        expect(page.locator("#view-analysis")).to_be_visible()
        page.goto(f"{base_url}/overview", wait_until="networkidle")
        expect(page.locator("#model-status")).to_have_text("Model ready")
        summary = page.request.get(f"{base_url}/api/summary").json()
        expect(page.locator(".kpi-value").first).to_have_text(f"{summary['dataset']['rows']:,}")
        expect(page.locator("#customer-rows .inspect-button")).to_have_count(8)
        assert_no_overflow(page)
        page.screenshot(path=str(output / "overview-desktop.png"), full_page=True)
        checks.append("overview shows actual API statistics and held-out records")

        expect(page.locator("#cohort-chart svg")).to_be_visible()
        cohort = page.request.get(f"{base_url}/api/cohorts").json()
        expect(page.locator("#cohort-count")).to_contain_text(f"{cohort['count']:,}")
        page.locator("#cohort-filters button[data-contract='Two year']").click()
        filtered = page.request.get(f"{base_url}/api/cohorts?contract=Two%20year").json()
        expect(page.locator("#cohort-count")).to_contain_text(f"{filtered['count']:,}")
        page.locator("#cohort-filters button[data-contract='']").click()
        expect(page.locator("#cohort-count")).to_contain_text(f"{cohort['count']:,}")
        page.evaluate("window.__cohortDelays = [600, 0]")
        page.locator("#cohort-filters button[data-contract='Month-to-month']").click()
        page.locator("#cohort-filters button[data-contract='']").click()
        page.wait_for_timeout(700)
        expect(page.locator("#cohort-count")).to_contain_text(f"{cohort['count']:,}")
        page.evaluate("window.__failNextCohort = true")
        page.locator("#cohort-filters button[data-contract='Two year']").click()
        expect(page.locator("#cohort-chart")).to_contain_text("Chart unavailable")
        page.set_viewport_size({"width": 1400, "height": 1100})
        expect(page.locator("#cohort-chart svg")).to_have_count(0)
        expect(page.locator("#cohort-data tr")).to_have_count(0)
        page.set_viewport_size({"width": 1440, "height": 1100})
        page.locator("#cohort-filters button[data-contract='']").click()
        expect(page.locator("#cohort-chart svg")).to_be_visible()
        navigate(page, "analysis")
        page.go_back()
        expect(page.locator("#view-overview")).to_be_visible()
        checks.append("real cohort chart/filter counts and browser history navigation")

        first_id = page.locator("#customer-rows .customer-id").first.inner_text()
        page.locator("#customer-search").fill(first_id)
        expect(page.locator("#customer-rows .inspect-button")).to_have_count(1)
        page.locator("#customer-search").fill("no-matching-id")
        expect(page.locator("#customer-rows")).to_contain_text("No customers match")
        page.locator("#customer-search").fill("")
        expect(page.locator("#customer-rows .inspect-button")).to_have_count(8)
        page.locator("#contract-filter").select_option("Two year")
        expect(page.locator("#customer-rows tr").first).to_contain_text("Two year")
        page.locator("#risk-filter").select_option("Low")
        expect(page.locator("#customer-rows .inspect-button").first).to_be_visible()
        page.locator("#next-page").click()
        expect(page.locator("#pagination-label")).to_contain_text("9–16")
        page.locator("#previous-page").click()
        expect(page.locator("#pagination-label")).to_contain_text("1–8")
        checks.append("search, empty state, contract/risk filters and pagination")

        page.locator("#customer-rows .inspect-button").first.click()
        expect(page.locator(".score-number")).to_be_visible()
        schema = page.request.get(f"{base_url}/api/schema").json()
        expect(page.locator(".factor-row")).to_have_count(len(schema["fields"]))
        expect(page.locator("#analysis-source")).to_contain_text("Held-out customer")
        expect(page.locator(".explanation-reconciliation")).to_contain_text("Reconstructed probability")
        assert_no_overflow(page)
        page.screenshot(path=str(output / "analysis-desktop.png"), full_page=True)
        page.locator("#field-MonthlyCharges").fill("80")
        expect(page.locator("#profile-label")).to_have_text("User scenario")
        expect(page.locator("#prediction-result")).to_contain_text("Inputs changed.")
        page.locator("#field-InternetService").select_option("No")
        for name in ("OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"):
            expect(page.locator(f"#field-{name}")).to_have_value("No internet service")
            expect(page.locator(f"#field-{name}")).to_be_disabled()
        page.locator("#field-PhoneService").select_option("No")
        expect(page.locator("#field-MultipleLines")).to_have_value("No phone service")
        page.locator("#predict-button").click()
        expect(page.locator(".score-number")).to_be_visible()
        expect(page.locator(".score-caption")).to_contain_text("User scenario")
        expect(page.locator("#prediction-error")).to_be_hidden()
        checks.append("held-out prediction, all SHAP factors, scenario state and service consistency")

        page.evaluate("window.__predictionDelays = [600]")
        page.locator("#predict-button").click()
        expect(page.locator(".score-number")).to_have_count(0)
        page.locator("#field-MonthlyCharges").fill("90")
        expect(page.locator("#predict-button")).to_be_enabled()
        expect(page.locator("#prediction-result")).to_contain_text("Inputs changed.")
        expect(page.locator(".score-number")).to_have_count(0)
        page.evaluate("window.__predictionDelays = [900, 0]")
        page.locator("#load-example").click()
        expect(page.locator("#predict-button")).to_be_disabled()
        expect(page.locator(".score-number")).to_have_count(0)
        navigate(page, "overview")
        next_id = page.locator("#customer-rows .customer-id").first.inner_text()
        page.locator("#customer-rows .inspect-button").first.click()
        expect(page.locator(".score-number")).to_be_visible()
        expect(page.locator("#load-example")).to_be_enabled()
        expect(page.locator("#profile-label")).to_have_text(next_id)
        customer = page.request.get(f"{base_url}/api/customers/{next_id}").json()
        expect(page.locator(".score-number")).to_have_text(f"{customer['probability'] * 100:.1f}%")
        checks.append("delayed real responses cannot retain old scores or overwrite newer inputs/customers")

        navigate(page, "batch")
        with page.expect_download() as sample_download:
            page.get_by_role("link", name="Download sample CSV").click()
        sample_path = output / "sample.csv"
        sample_download.value.save_as(str(sample_path))
        source_rows = list(csv.DictReader(io.StringIO(sample_path.read_text(encoding="utf-8-sig"))))
        assert source_rows
        page.locator("#batch-file").set_input_files(str(sample_path))
        with page.expect_download() as results_download:
            page.locator("#batch-button").click()
        results_path = output / "predictions.csv"
        results_download.value.save_as(str(results_path))
        rows = list(csv.DictReader(io.StringIO(results_path.read_text(encoding="utf-8-sig"))))
        assert len(rows) == len(source_rows)
        assert all(0 <= float(row["churn_probability"]) <= 1 for row in rows)
        expect(page.locator("#batch-message")).to_contain_text("Scoring complete")
        page.locator("#batch-file").set_input_files({"name": "invalid.csv", "mimeType": "text/csv", "buffer": b"invalid,column\n1,2\n"})
        page.locator("#batch-button").click()
        expect(page.locator("#batch-message.error")).to_be_visible()
        expect(page.locator("#batch-button")).to_be_enabled()
        checks.append("sample download, real batch export and invalid CSV error")

        navigate(page, "models")
        expect(page.locator("#model-comparison tr")).to_have_count(len(summary["models"]))
        comparison = page.locator("#model-comparison").locator("xpath=ancestor::table")
        assert comparison.locator("thead th").count() == comparison.locator("tbody tr").first.locator("td").count()
        expect(comparison.locator("thead")).to_contain_text("Test accuracy")
        expect(comparison.locator("thead")).to_contain_text("Test Brier")
        expect(page.locator(".matrix-cell")).to_have_count(4)
        for image in page.locator("#evaluation-charts img").all():
            image.scroll_into_view_if_needed()
            expect(image).to_be_visible()
            image.evaluate("img => img.complete || new Promise(resolve => img.addEventListener('load', resolve, {once: true}))")
            assert image.evaluate("img => img.naturalWidth > 0")
        for link in page.locator("a[href^='/docs/']").all():
            target = f"{base_url}{link.get_attribute('href')}"
            assert page.request.get(target).ok, target
        checks.append("comparison, confusion matrix, actual plot images and documentation links")

        for width in (1440, 1024, 768, 390, 320):
            page.set_viewport_size({"width": width, "height": 950})
            for view in ("overview", "analysis", "batch", "models"):
                navigate(page, view)
                expect(page.locator(f"#view-{view}")).to_be_visible()
                assert_no_overflow(page)
                if view == "overview" and width < 600:
                    page.wait_for_function("""() => {
                      const chart=document.querySelector('#cohort-chart');
                      return chart.querySelector('svg')?.viewBox.baseVal.width === chart.clientWidth;
                    }""")
                    labels = page.locator("#cohort-chart svg text").evaluate_all("""nodes => nodes
                      .filter(n=>n.textContent.includes('–')).map(n=>{
                        const r=n.getBoundingClientRect(); return {left:r.left,right:r.right};
                      })""")
                    assert all(a["right"] <= b["left"] for a, b in pairwise(labels)), labels
            if width == 390:
                navigate(page, "overview")
                page.wait_for_function("() => document.querySelector('#sidebar').getBoundingClientRect().right <= 1")
                page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                mobile_geometry = page.evaluate("({height:document.documentElement.scrollHeight, body:document.body.getBoundingClientRect().height, y:scrollY})")
                page.screenshot(path=str(output / "overview-mobile.png"), full_page=True)
        checks.append("four views fit 1440/1024/768/390/320 pixel viewports")

        for width in (390, 320):
            page.set_viewport_size({"width": width, "height": 950})
            for path in ("", "guide"):
                page.goto(f"{base_url}/{path}", wait_until="networkidle")
                assert_no_overflow(page)
                if width == 390:
                    filename = "guide-mobile.png" if path else "home-mobile.png"
                    page.screenshot(path=str(output / filename), full_page=True)
        checks.append("product home and guide fit narrow mobile screens; legacy root links redirect")

        page.set_viewport_size({"width": 1440, "height": 1000})
        page.goto(f"{base_url}/overview")
        page.keyboard.press("Tab")
        expect(page.locator(".skip-link")).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.locator("#main")).to_be_focused()
        checks.append("keyboard skip link and focus target")
        # Invalid-upload HTTP 400 is expected; JavaScript exceptions are never ignored.
        unexpected = [message for message in errors if "status of 400" not in message]
        assert not unexpected, unexpected
        browser.close()
    result = {"base_url": base_url, "checks": checks, "unexpected_console_errors": unexpected,
              "mobile_geometry": mobile_geometry,
              "screenshots": ["home-desktop.png", "overview-desktop.png", "analysis-desktop.png",
                              "overview-mobile.png", "home-mobile.png", "guide-mobile.png"]}
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5050")
    print(json.dumps(check_dashboard(parser.parse_args().url.rstrip("/")), indent=2))
