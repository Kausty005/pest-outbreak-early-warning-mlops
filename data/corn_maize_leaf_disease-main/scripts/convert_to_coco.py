#!/usr/bin/env python3
"""
Convert corn_maize_leaf_disease dataset annotations to COCO JSON format.
Supports multi-class classification (4 classes: healthy, gray_leaf_spot, common_rust, blight).
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

def read_split_list(split_file: Path) -> List[str]:
    """Read image base names (without extension) from a split file."""
    if not split_file.exists():
        return []
    lines = [line.strip() for line in split_file.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]

def image_size(image_path: Path) -> Tuple[int, int]:
    """Return (width, height) for an image path using PIL."""
    with Image.open(image_path) as img:
        return img.width, img.height

def parse_csv_boxes(csv_path: Path) -> List[Dict]:
    """Parse a single CSV file and return bounding boxes with category IDs."""
    if not csv_path.exists():
        return []
    
    boxes = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Support multiple column name variants
                x = float(row.get('x', row.get('xc', row.get('x_center', 0))))
                y = float(row.get('y', row.get('yc', row.get('y_center', 0))))
                width = float(row.get('width', row.get('w', row.get('dx', 0))))
                height = float(row.get('height', row.get('h', row.get('dy', 0))))
                label = int(row.get('label', row.get('class', row.get('category_id', 1))))
                
                if width > 0 and height > 0:
                    boxes.append({
                        'bbox': [x, y, width, height],
                        'area': width * height,
                        'category_id': label
                    })
            except (ValueError, KeyError):
                continue
    
    return boxes

def collect_annotations_for_split(
    category_root: Path,
    split: str,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Collect COCO dictionaries for images, annotations, and categories.
    Supports structure: corn_leaves/{subcategory}/ subdirectories.
    Each subcategory has its own sets/ directory with split files.
    """
    # Try to read from subcategory-specific sets directories first
    image_stems = set()
    subcategory_names = ['healthy', 'gray_leaf_spot', 'common_rust', 'blight']
    
    for subcat_name in subcategory_names:
        subcat_dir = category_root / subcat_name
        subcat_sets_dir = subcat_dir / "sets"
        split_file = subcat_sets_dir / f"{split}.txt"
        
        if split_file.exists():
            stems = read_split_list(split_file)
            image_stems.update(stems)
    
    # Fallback: try category-level sets directory
    if not image_stems:
        sets_dir = category_root / "sets"
        split_file = sets_dir / f"{split}.txt"
        if split_file.exists():
            image_stems = set(read_split_list(split_file))
    
    # Final fallback: use all images if no split file
    if not image_stems:
        image_stems = set()
        for subcategory_dir in category_root.glob("*"):
            if subcategory_dir.is_dir() and subcategory_dir.name != "sets":
                images_dir = subcategory_dir / "images"
                if images_dir.exists():
                    image_stems.update({p.stem for p in images_dir.glob("*.png")})
                    image_stems.update({p.stem for p in images_dir.glob("*.jpg")})
                    image_stems.update({p.stem for p in images_dir.glob("*.JPG")})
                    image_stems.update({p.stem for p in images_dir.glob("*.jpeg")})
                    image_stems.update({p.stem for p in images_dir.glob("*.JPEG")})
    
    images: List[Dict] = []
    anns: List[Dict] = []
    categories: List[Dict] = [
        {"id": 1, "name": "healthy", "supercategory": "corn"},
        {"id": 2, "name": "gray_leaf_spot", "supercategory": "corn"},
        {"id": 3, "name": "common_rust", "supercategory": "corn"},
        {"id": 4, "name": "blight", "supercategory": "corn"}
    ]
    
    image_id_counter = 1
    ann_id_counter = 1
    
    # Check all subcategory directories
    subcategory_names = ['healthy', 'gray_leaf_spot', 'common_rust', 'blight']
    
    for stem in sorted(image_stems):
        # Try each subcategory directory
        img_path = None
        subcategory = None
        csv_path = None
        
        for subcat_name in subcategory_names:
            subcat_dir = category_root / subcat_name
            for ext in ['.png', '.jpg', '.JPG', '.PNG', '.jpeg', '.JPEG']:
                test_path = subcat_dir / 'images' / f"{stem}{ext}"
                if test_path.exists():
                    img_path = test_path
                    subcategory = subcat_name
                    csv_path = subcat_dir / 'csv' / f"{stem}.csv"
                    break
            if img_path:
                break
        
        if not img_path:
            continue
        
        width, height = image_size(img_path)
        images.append({
            "id": image_id_counter,
            "file_name": f"corn_leaves/{subcategory}/images/{img_path.name}",
            "width": width,
            "height": height,
        })
        
        if csv_path and csv_path.exists():
            for box in parse_csv_boxes(csv_path):
                anns.append({
                    "id": ann_id_counter,
                    "image_id": image_id_counter,
                    "category_id": box['category_id'],
                    "bbox": box['bbox'],
                    "area": box['area'],
                    "iscrowd": 0,
                })
                ann_id_counter += 1
        
        image_id_counter += 1
    
    return images, anns, categories

def build_coco_dict(
    images: List[Dict],
    anns: List[Dict],
    categories: List[Dict],
    description: str,
) -> Dict:
    """Build a complete COCO dict from components."""
    return {
        "info": {
            "year": 2025,
            "version": "1.0.0",
            "description": description,
            "url": "https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset",
        },
        "images": images,
        "annotations": anns,
        "categories": categories,
        "licenses": [],
    }

def main():
    parser = argparse.ArgumentParser(
        description="Convert corn_maize_leaf_disease dataset to COCO JSON format"
    )
    # Auto-detect root directory if script is in scripts/ subdirectory
    script_dir = Path(__file__).parent
    default_root = script_dir.parent if script_dir.name == "scripts" else Path(".")
    
    parser.add_argument(
        "--root",
        type=str,
        default=str(default_root),
        help=f"Root directory of the dataset (default: {default_root})",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="annotations",
        help="Output directory for COCO JSON files (default: annotations)",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        help="Dataset splits to process (default: train val test)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="corn_leaves",
        help="Category directory name (default: corn_leaves)",
    )
    
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    out_dir = root / args.out
    category_root = root / args.category
    
    if not category_root.exists():
        print(f"Error: Category directory {category_root} does not exist")
        sys.exit(1)
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Converting annotations from {category_root}")
    print(f"Output directory: {out_dir}")
    print(f"Splits: {args.splits}")
    
    for split in args.splits:
        print(f"\nProcessing {split} split...")
        images, anns, categories = collect_annotations_for_split(category_root, split)
        
        if not images:
            print(f"Warning: No images found for {split} split")
            continue
        
        description = f"Corn Maize Leaf Disease {split} split"
        coco_dict = build_coco_dict(images, anns, categories, description)
        
        output_file = out_dir / f"corn_leaves_instances_{split}.json"
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(coco_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Created {output_file}")
        print(f"  Images: {len(images)}")
        print(f"  Annotations: {len(anns)}")
        print(f"  Categories: {len(categories)}")
    
    print("\nConversion completed!")

if __name__ == "__main__":
    main()

