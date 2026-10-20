"""
train_maize_disease.py
──────────────────────
Root command-line runner to train the Maize Leaf Disease CNN classification model.

Usage:
    python train_maize_disease.py
    python train_maize_disease.py --epochs-stage1 6 --epochs-stage2 6 --batch-size 32
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.maize_disease.train import main

if __name__ == "__main__":
    main()
