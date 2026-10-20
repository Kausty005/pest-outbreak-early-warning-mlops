"""
predict.py
──────────
CLI and reusable prediction script for Maize Leaf Disease classification.

Usage:
    python predict.py path/to/leaf_image.jpg
    python predict.py path/to/leaf_image.jpg --json
    python predict.py --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.maize_disease.predict import (
    MaizeDiseasePredictor,
    DEFAULT_MODEL_PATH,
    DEFAULT_CLASS_NAMES_PATH,
)


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def format_cli_output(result: dict) -> str:
    lines = [
        "",
        "=" * 70,
        "   AgriAdapt AI -- Maize Leaf Disease Diagnostic Report",
        "=" * 70,
        f"  Image file:        {Path(result['image_path']).name}",
        f"  Predicted Class:   {result['predicted_class'].upper().replace('_', ' ')}",
        f"  Health Status:     {result['status']}",
        f"  Confidence Score:  {result['confidence']:.2%}",
        "-" * 70,
        "  Class Probability Distribution:",
    ]
    for item in result["class_probabilities"]:
        bar = "#" * int(item["score"] * 25)
        lines.append(f"    * {item['class']:<16} : {item['score']:>6.2%}  [{bar:<25}]")

    lines.extend([
        "-" * 70,
        f"  Advisory Note: {result['disclaimer']}",
        "=" * 70,
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Predict maize leaf disease from an input leaf image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("image_path", help="Path to input maize leaf image (.jpg, .jpeg, .png, etc.)")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="Path to trained .keras model file")
    parser.add_argument("--class-names", default=str(DEFAULT_CLASS_NAMES_PATH), help="Path to class_names.json")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Input image does not exist: {image_path}", file=sys.stderr)
        return 1

    try:
        predictor = MaizeDiseasePredictor(
            model_path=args.model,
            class_names_path=args.class_names,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error initializing predictor: {e}", file=sys.stderr)
        return 1

    try:
        result = predictor.predict(image_path)
    except Exception as e:
        print(f"Prediction failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_cli_output(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
