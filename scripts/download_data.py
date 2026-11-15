"""Download the unmodified canonical IBM sample with pinned integrity and provenance."""

import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
API_URL = "https://api.github.com/repos/IBM/telco-customer-churn-on-icp4d/contents/data/Telco-Customer-Churn.csv?ref=master"
EXPECTED_SHA256 = "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"


def download(root: Path = ROOT) -> Path:
    """Reuse an integrity-checked local CSV or download over HTTPS with an API fallback."""
    destination = root / "data/raw/Telco-Customer-Churn.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        payload = destination.read_bytes()
        transport = "existing integrity-checked file"
    else:
        errors: list[str] = []
        for url in [SOURCE_URL, API_URL]:
            try:
                request = Request(url, headers={"User-Agent": "college-telecom-churn-project", "Accept": "application/vnd.github+json"})
                with urlopen(request, timeout=20) as response:
                    payload = response.read(2_000_000)
                if url == API_URL:
                    payload = base64.b64decode(json.loads(payload)["content"], validate=False)
                transport = url
                break
            except (URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        else:
            raise RuntimeError("Dataset download failed; no synthetic fallback is used. " + " | ".join(errors))
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Dataset SHA-256 mismatch: {digest}; expected {EXPECTED_SHA256}. Refusing changed data.")
    if not destination.exists():
        temporary = destination.with_suffix(".part")
        temporary.write_bytes(payload)
        temporary.replace(destination)
    provenance = root / "data/provenance.json"
    if not provenance.exists():
        provenance.write_text(json.dumps({
            "source_url": SOURCE_URL, "download_transport": transport, "sha256": digest,
            "bytes": len(payload), "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "source_repository": "https://github.com/IBM/telco-customer-churn-on-icp4d",
            "license_url": "https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE",
            "license": "Apache-2.0 (source repository)", "description": "IBM fictional telecom sample; not live customer data",
        }, indent=2), encoding="utf-8")
    return destination


if __name__ == "__main__":
    print(download())
