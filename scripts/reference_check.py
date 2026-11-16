"""Capture the real website and compare its geometry with the saved UI reference."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def compare_reference(base_url: str) -> dict:
    """Measure reference-led layout targets; never synthesize screenshot content."""
    output = ROOT / "artifacts/references"
    reference = json.loads((output / "shadcn-measurements.json").read_text())
    selectors = {"sidebar": ".sidebar", "workspace": ".shell", "header": ".topbar",
                 "card": ".kpi-card", "value": ".kpi-value"}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(f"{base_url}/overview", wait_until="networkidle")
        expect(page.locator("#model-status")).to_have_text("Model ready")
        expect(page.locator("#cohort-chart svg")).to_be_visible()
        page.evaluate("document.fonts.ready")
        measured = {}
        for name, selector in selectors.items():
            measured[name] = page.locator(selector).first.evaluate("""el => {
                const r=el.getBoundingClientRect(), s=getComputedStyle(el);
                return {x:r.x,y:r.y,width:r.width,height:r.height,fontSize:parseFloat(s.fontSize),
                        fontFamily:s.fontFamily,borderRadius:s.borderRadius};
            }""")
        measured["fonts"] = page.evaluate("[...document.fonts].map(f=>({family:f.family,status:f.status}))")
        page.screenshot(path=str(output / "retain-dashboard-v2.png"))
        browser.close()
    targets = [
        ("Sidebar width", reference['[data-slot="sidebar-container"]']["width"], measured["sidebar"]["width"]),
        ("Workspace left", reference['[data-slot="sidebar-inset"]']["x"], measured["workspace"]["x"]),
        ("Workspace top", reference['[data-slot="sidebar-inset"]']["y"], measured["workspace"]["y"]),
        ("Header height", reference["header"]["height"], measured["header"]["height"]),
        ("First card left", reference['[data-slot="card"]']["x"], measured["card"]["x"]),
        ("First card top", reference['[data-slot="card"]']["y"], measured["card"]["y"]),
        ("Card height", reference['[data-slot="card"]']["height"], measured["card"]["height"]),
        ("Card width", reference['[data-slot="card"]']["width"], measured["card"]["width"]),
        ("KPI font size", 30, measured["value"]["fontSize"]),
    ]
    checks = [{"element": name, "reference_px": expected, "actual_px": actual,
               "within_one_pixel": abs(expected - actual) <= 1} for name, expected, actual in targets]
    result = {"reference_url": "https://ui.shadcn.com/view/new-york-v4/dashboard-01",
              "viewport": {"width": 1440, "height": 1000}, "measurements": measured, "checks": checks}
    (output / "match-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output / "comparison.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Reference and actual Retain website</title><style>body{margin:0;font:14px system-ui;background:#eee}
main{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}img{width:100%;display:block}
h1{font-size:18px;margin:16px}h2{font-size:14px;margin:0;padding:12px;background:white}</style>
<h1>Actual browser captures at the same 1440 × 1000 viewport</h1><main>
<section><h2>Official shadcn dashboard-01 reference</h2><img src="shadcn-dashboard-01.png" alt="Official reference"></section>
<section><h2>Retain implementation — actual model and dataset values</h2><img src="retain-dashboard-v2.png" alt="Actual Retain website"></section>
</main></html>''', encoding="utf-8")
    assert all(item["within_one_pixel"] for item in checks), checks
    assert any(font["family"] == "Geist" and font["status"] == "loaded" for font in measured["fonts"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5050")
    print(json.dumps(compare_reference(parser.parse_args().url.rstrip("/")), indent=2))
