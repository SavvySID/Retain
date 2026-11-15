"""Download, train, evaluate and export the reproducible college-project model."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from download_data import download

from churn.training import train

if __name__ == "__main__":
    train(ROOT, download(ROOT))
