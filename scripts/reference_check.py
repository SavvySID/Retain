"""Capture V3 reference/website evidence and check basic UI finish requirements."""

import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def rgb(value: str) -> tuple[float, ...]:
    """Read opaque Chromium RGB output; refuse unsupported/transparent samples."""
    channels = tuple(float(item) for item in re.findall(r"[\d.]+", value))
    if not value.startswith("rgb") or len(channels) not in (3, 4):
        raise ValueError(f"Unsupported computed color: {value}")
    if len(channels) == 4 and channels[3] != 1:
        raise ValueError(f"Contrast sample must have an opaque background: {value}")
    return channels[:3]


def contrast(foreground: tuple[float, ...], background: tuple[float, ...]) -> float:
    """Calculate WCAG relative-luminance contrast for two opaque RGB colors."""
    def luminance(color: tuple[float, ...]) -> float:
        """Convert sRGB components to linear-light luminance."""
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                  for v in (channel / 255 for channel in color)]
        return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))
    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def compare_reference(base_url: str) -> dict:
    """Capture actual pages, hierarchy/contrast and viewport fit; do not invent a similarity score."""
    assert contrast((0, 0, 0), (255, 255, 255)) == 21
    assert contrast((42, 42, 42), (42, 42, 42)) == 1
    output = ROOT / "artifacts/references/v3"
    output.mkdir(parents=True, exist_ok=True)
    results: dict = {"base_url": base_url, "references": ["https://attio.com/",
                    "https://www.vitally.io/features/reporting"], "pages": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        for name, path in (("home", "/"), ("overview", "/overview")):
            page.goto(f"{base_url}{path}", wait_until="networkidle")
            if name == "home":
                expect(page.locator("#home-hero")).to_be_visible()
                expect(page.locator("#home-cohort-chart svg")).to_be_visible()
                expect(page.locator("#home-factors .home-factor").first).to_be_attached()
            else:
                expect(page.locator("#model-status")).to_have_text("Model ready")
            page.evaluate("() => document.fonts.ready")
            data = page.evaluate("""() => {
              const body=getComputedStyle(document.body), h=document.querySelector('h1');
              const heading=getComputedStyle(h), button=document.querySelector('.button-primary');
              const action=getComputedStyle(button);
              return {bodyColor:body.color,bodyBackground:body.backgroundColor,font:body.fontFamily,
                headingSize:parseFloat(heading.fontSize),buttonColor:action.color,
                buttonBackground:action.backgroundColor,width:innerWidth,documentWidth:document.documentElement.scrollWidth,
                fonts:[...document.fonts].map(f=>({family:f.family,status:f.status}))};
            }""")
            data["text_contrast"] = contrast(rgb(data["bodyColor"]), rgb(data["bodyBackground"]))
            data["button_contrast"] = contrast(rgb(data["buttonColor"]), rgb(data["buttonBackground"]))
            assert data["text_contrast"] >= 4.5, data
            assert data["button_contrast"] >= 4.5, data
            assert data["documentWidth"] <= data["width"], data
            assert any(font["family"] == "Geist" and font["status"] == "loaded" for font in data["fonts"])
            if name == "home":
                assert data["headingSize"] >= 48, data
            page.screenshot(path=str(output / f"retain-{name}-desktop.png"))
            page.screenshot(path=str(output / f"retain-{name}-full.png"), full_page=True)
            results["pages"].append({"page": name, "viewport": "1440x1000", **data})
        for name, path in (("home", "/"), ("overview", "/overview")):
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(f"{base_url}{path}", wait_until="networkidle")
            assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(output / f"retain-{name}-mobile.png"), full_page=True)
        browser.close()
    (output / "finish-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output / "comparison.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Related references and actual Retain V3</title><style>body{margin:0;font:14px system-ui;background:#f4f5f1}
main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px}img{width:100%;display:block}
h1{font-size:20px;margin:20px}h2{font-size:14px;padding:12px;background:white;margin:0}</style>
<h1>Related product references and actual Retain captures at 1440 x 1000</h1><main>
<section><h2>Attio: editorial hero and product-first presentation</h2><img src="attio-home-desktop.png" alt="Attio reference"></section>
<section><h2>Retain V3: own brand and actual local model data</h2><img src="retain-home-desktop.png" alt="Actual Retain home"></section>
<section><h2>Vitally reporting: account investigation workflow reference</h2><img src="vitally-reporting-desktop.png" alt="Vitally reference"></section>
<section><h2>Retain analyst workspace</h2><img src="retain-overview-desktop.png" alt="Actual Retain overview"></section>
</main></html>''', encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5050")
    print(json.dumps(compare_reference(parser.parse_args().url.rstrip("/")), indent=2))
