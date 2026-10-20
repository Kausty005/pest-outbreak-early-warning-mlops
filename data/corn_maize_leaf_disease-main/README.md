# Corn Maize Leaf Disease Classification

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green?logo=creativecommons&logoColor=white)](https://creativecommons.org/licenses/by/4.0/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?logo=semver&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease)
[![GitHub stars](https://img.shields.io/github/stars/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Stars&color=orange&labelColor=orange&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease)
[![GitHub forks](https://img.shields.io/github/forks/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Forks&color=yellow&labelColor=yellow&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease)
[![GitHub watchers](https://img.shields.io/github/watchers/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Watchers&color=cyan&labelColor=cyan&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease)
[![GitHub issues](https://img.shields.io/github/issues/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Issues&color=red&labelColor=red&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=PRs&color=lime&labelColor=lime&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Contributors&color=purple&labelColor=purple&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/your-repo/corn_maize_leaf_disease?style=flat&logo=github&label=Last%20Commit&color=gray&labelColor=gray&logoColor=white)](https://github.com/your-repo/corn_maize_leaf_disease/commits)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.xxxxx-indigo?logo=doi&logoColor=white)](https://doi.org/10.5281/zenodo.xxxxx)

A dataset of corn/maize leaf images for disease classification, collected and organized for computer vision and deep learning research in agricultural applications.

- **Project page**: `https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset`
- **Dataset repository**: `https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset`

## TL;DR

- **Task**: Classification (four classes: `healthy`, `gray_leaf_spot`, `common_rust`, `blight`)
- **Modality**: RGB
- **Platform**: Handheld/field
- **Real/Synthetic**: Real
- **Images**: 4,188 labeled images
- **Classes**: 4 disease categories
  - `healthy`: 1,162 images
  - `gray_leaf_spot`: 574 images
  - `common_rust`: 1,306 images
  - `blight`: 1,146 images
- **Resolution**: 256×256 pixels (most images)
- **Annotations**: COCO JSON (image-level via full-image boxes)
- **License**: CC BY 4.0 (see LICENSE)
- **Citation**: See below

## Table of Contents

- [Download](#download)
- [Dataset Structure](#dataset-structure)
- [Sample Images](#sample-images)
- [Annotation Schema](#annotation-schema)
- [Stats and Splits](#stats-and-splits)
- [Quick Start](#quick-start)
- [Evaluation and Baselines](#evaluation-and-baselines)
- [Datasheet (Data Card)](#datasheet-data-card)
- [Known Issues and Caveats](#known-issues-and-caveats)
- [License](#license)
- [Citation](#citation)
- [Changelog](#changelog)
- [Contact](#contact)

## Download

- **Original dataset**: `https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset`
- **This repository**: Hosts structure and conversion scripts only; place the downloaded folders under this directory.
- **Local license file**: See `LICENSE` (CC BY 4.0).

## Dataset Structure

This dataset follows the standardized dataset structure specification with subcategory organization:

```
corn_maize_leaf_disease/
├── corn_leaves/            # Main category directory
│   ├── healthy/            # Healthy corn leaves
│   │   ├── csv/            # CSV annotations per image
│   │   ├── json/           # JSON annotations per image
│   │   ├── images/         # Healthy images
│   │   └── sets/           # Dataset splits for healthy
│   │       ├── train.txt
│   │       ├── val.txt
│   │       ├── test.txt
│   │       ├── all.txt
│   │       └── train_val.txt
│   ├── gray_leaf_spot/     # Gray leaf spot disease
│   │   ├── csv/
│   │   ├── json/
│   │   ├── images/
│   │   └── sets/           # Dataset splits for gray_leaf_spot
│   ├── common_rust/        # Common rust disease
│   │   ├── csv/
│   │   ├── json/
│   │   ├── images/
│   │   └── sets/           # Dataset splits for common_rust
│   ├── blight/             # Blight disease
│   │   ├── csv/
│   │   ├── json/
│   │   ├── images/
│   │   └── sets/           # Dataset splits for blight
│   └── labelmap.json       # Label mapping (healthy=1, gray_leaf_spot=2, common_rust=3, blight=4)
├── data/                   # Original data directory
│   └── origin/             # Original dataset files
│       ├── Blight/
│       ├── Common_Rust/
│       ├── Gray_Leaf_Spot/
│       └── Healthy/
├── annotations/            # COCO format JSON (generated)
│   ├── corn_leaves_instances_train.json
│   ├── corn_leaves_instances_val.json
│   └── corn_leaves_instances_test.json
├── scripts/
│   ├── convert_to_coco.py     # COCO conversion script
│   └── generate_coco_annotations.py  # Original annotation generation script (legacy)
├── LICENSE
├── README.md
└── requirements.txt
```

- Splits: Each subcategory has its own `sets/` directory with split files (`train.txt`, `val.txt`, `test.txt`, `all.txt`, `train_val.txt`) listing image basenames (no extension). If missing, all images are used.

## Sample Images

Below are example images for each category in this dataset. Paths are relative to this README location.

<table>
  <tr>
    <th>Category</th>
    <th>Sample</th>
  </tr>
  <tr>
    <td><strong>Healthy</strong></td>
    <td>
      <img src="corn_leaves/healthy/images/Corn_Health (1063).jpg" alt="Healthy example" width="260"/>
      <div align="center"><code>corn_leaves/healthy/images/Corn_Health (1063).jpg</code></div>
    </td>
  </tr>
  <tr>
    <td><strong>Gray Leaf Spot</strong></td>
    <td>
      <img src="corn_leaves/gray_leaf_spot/images/Corn_Gray_Spot (1).jpg" alt="Gray Leaf Spot example" width="260"/>
      <div align="center"><code>corn_leaves/gray_leaf_spot/images/Corn_Gray_Spot (1).jpg</code></div>
    </td>
  </tr>
  <tr>
    <td><strong>Common Rust</strong></td>
    <td>
      <img src="corn_leaves/common_rust/images/Corn_Common_Rust (1).jpg" alt="Common Rust example" width="260"/>
      <div align="center"><code>corn_leaves/common_rust/images/Corn_Common_Rust (1).jpg</code></div>
    </td>
  </tr>
  <tr>
    <td><strong>Blight</strong></td>
    <td>
      <img src="corn_leaves/blight/images/Corn_Blight (783).JPG" alt="Blight example" width="260"/>
      <div align="center"><code>corn_leaves/blight/images/Corn_Blight (783).JPG</code></div>
    </td>
  </tr>
</table>

## Annotation Schema

- **CSV per-image schemas** (stored under each category's `csv/` folder):
  - Classification task: columns include `item, x, y, width, height, label` (full-image bounding box: `[0, 0, image_width, image_height]`).
- **COCO-style** (generated):
```json
{
  "info": {
    "year": 2025,
    "version": "1.0.0",
    "description": "Corn Maize Leaf Disease train split",
    "url": "https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset"
  },
  "images": [
    {
      "id": 1,
      "file_name": "corn_leaves/healthy/images/Corn_Health (1063).jpg",
      "width": 256,
      "height": 256
    }
  ],
  "categories": [
    {"id": 1, "name": "healthy", "supercategory": "corn"},
    {"id": 2, "name": "gray_leaf_spot", "supercategory": "corn"},
    {"id": 3, "name": "common_rust", "supercategory": "corn"},
    {"id": 4, "name": "blight", "supercategory": "corn"}
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [0, 0, 256, 256],
      "area": 65536,
      "iscrowd": 0
    }
  ]
}
```

- **Label maps**: `corn_leaves/labelmap.json` defines the category mapping; the provided converter normalizes to 4 categories (healthy=1, gray_leaf_spot=2, common_rust=3, blight=4).

## Stats and Splits

- **Total images**: 4,188
  - Healthy: 1,162 images
  - Gray Leaf Spot: 574 images
  - Common Rust: 1,306 images
  - Blight: 1,146 images
- **Training set**: 2,931 images (distributed across subcategories)
- **Validation set**: 628 images (distributed across subcategories)
- **Test set**: 629 images (distributed across subcategories)
- **Classes**: 4 (healthy=1, gray_leaf_spot=2, common_rust=3, blight=4)
- Splits provided via `corn_leaves/{subcategory}/sets/*.txt`. Each subcategory has its own split files. You may define your own splits by editing those files.

**Note**: The dataset is slightly imbalanced, with Common Rust having the most samples and Gray Leaf Spot having the fewest.

## Quick Start

### Using COCO API

```python
from pycocotools.coco import COCO
import json

# Load COCO annotations
coco = COCO('annotations/corn_leaves_instances_train.json')

# Get all image IDs
img_ids = coco.getImgIds()

# Get annotations for first image
ann_ids = coco.getAnnIds(imgIds=img_ids[0])
anns = coco.loadAnns(ann_ids)

# Load image info
img_info = coco.loadImgs(img_ids[0])[0]
print(f"Image: {img_info['file_name']}")
print(f"Size: {img_info['width']}x{img_info['height']}")
```

### Converting to COCO format

If you need to regenerate COCO annotations from CSV files:

```bash
python scripts/convert_to_coco.py --root . --out annotations \
    --category corn_leaves --splits train val test
```

### Dependencies

**Required**:
- `Pillow>=9.5` (for image processing)

**Optional**:
- `pycocotools>=2.0.7` (for COCO API)

Install with:
```bash
pip install -r requirements.txt
```

## Evaluation and Baselines

- **Primary metric**: Classification accuracy
- **Baseline results**: See Kaggle dataset page for baseline results.

## Datasheet (Data Card)

### Motivation

This dataset was created to support research in automated corn leaf disease detection and classification, which is crucial for helping farmers quickly identify plant diseases to prevent crop loss and ensure food security.

### Composition

The dataset consists of:
- **Image types**: RGB images of corn/maize leaves showing various disease conditions
- **Categories**: 4 classes (healthy, gray_leaf_spot, common_rust, blight)
- **Annotation format**: Full-image bounding boxes for classification tasks

### Collection Process

- **Source**: Field images of corn leaves collected from various sources; part of Kaggle dataset
- **Annotation tool**: Custom script generating COCO format annotations
- **Validation**: Manual validation of images and annotations

### Preprocessing

- Images standardized to 256×256 pixels
- COCO JSON annotations produced by conversion script
- Full-image bounding boxes used for classification tasks

### Distribution

- Dataset is distributed under CC BY 4.0 license
- Original data hosted on Kaggle
- This repository provides ancillary scripts and standardized structure

### Maintenance

- Dataset structure has been standardized according to the dataset structure specification
- COCO format annotations are generated from CSV files using the provided conversion script

## Known Issues and Caveats

- **Classification task**: This is a classification dataset. Each image has a full-image bounding box annotation indicating its class.
- **Dataset imbalance**: The dataset is slightly imbalanced, with Common Rust having the most samples (1,306) and Gray Leaf Spot having the fewest (574).
- **Image format**: Images are in various formats (JPG, JPEG, PNG) with different case extensions. The conversion script handles all formats.
- **Coordinates**: Coordinates are in pixel units with origin at the image top-left. Ensure downstream tooling expects absolute COCO boxes.
- **File naming**: Original files use parentheses in names (e.g., `Corn_Health (1063).jpg`), which is preserved in the standardized structure.

## License

This dataset is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0). See `LICENSE` for the full license text.

Check the original dataset terms and cite appropriately.

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{corn_maize_leaf_disease_2025,
  title={Corn Maize Leaf Disease Classification Dataset},
  author={Smaranjit Ghose},
  year={2025},
  url={https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset},
  license={CC BY 4.0}
}
```

## Changelog

- **V1.0.0** (2025): Initial standardized structure and COCO conversion utility

## Contact

- **Maintainers**: Dataset maintainers
- **Original authors**: Smaranjit Ghose
- **Source**: `https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset`
