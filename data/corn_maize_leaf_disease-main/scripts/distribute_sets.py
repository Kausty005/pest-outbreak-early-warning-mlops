#!/usr/bin/env python3
"""
Distribute dataset split files to each subcategory directory.
Each subcategory will have its own sets/ directory with filtered split files.
"""

import shutil
from pathlib import Path

def distribute_sets(root_dir: Path):
    """Distribute sets files to each subcategory directory."""
    main_category = root_dir / "corn_leaves"
    sets_dir = main_category / "sets"
    
    if not sets_dir.exists():
        print(f"Warning: {sets_dir} does not exist.")
        print("This script distributes split files from corn_leaves/sets/ to each subcategory directory.")
        print("If sets files are already distributed to subcategory directories, this script is not needed.")
        print("To use this script, first create a combined sets/ directory with split files.")
        return
    
    # Subcategory mappings
    subcategories = {
        "healthy": "Corn_Health",
        "gray_leaf_spot": "Corn_Gray_Spot",
        "common_rust": "Corn_Common_Rust",
        "blight": "Corn_Blight"
    }
    
    # Read all split files
    split_files = ["train.txt", "val.txt", "test.txt", "all.txt", "train_val.txt"]
    
    for subcat_name, prefix in subcategories.items():
        subcat_dir = main_category / subcat_name
        subcat_sets_dir = subcat_dir / "sets"
        subcat_sets_dir.mkdir(exist_ok=True)
        
        # Get all images in this subcategory
        images_dir = subcat_dir / "images"
        if not images_dir.exists():
            print(f"Warning: {images_dir} does not exist, skipping {subcat_name}")
            continue
        
        # Get all image stems for this subcategory
        image_stems = set()
        for ext in ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']:
            for img_path in images_dir.glob(f"*{ext}"):
                # Extract stem, handling the prefix pattern
                stem = img_path.stem
                image_stems.add(stem)
        
        print(f"Processing {subcat_name}: {len(image_stems)} images")
        
        # Filter each split file
        for split_file in split_files:
            source_file = sets_dir / split_file
            if not source_file.exists():
                continue
            
            # Read all lines from source file
            with open(source_file, 'r', encoding='utf-8') as f:
                all_lines = [line.strip() for line in f if line.strip()]
            
            # Filter lines that belong to this subcategory
            filtered_lines = []
            for line in all_lines:
                # Check if this image belongs to this subcategory
                if line in image_stems:
                    filtered_lines.append(line)
            
            # Write filtered file
            target_file = subcat_sets_dir / split_file
            with open(target_file, 'w', encoding='utf-8') as f:
                for line in filtered_lines:
                    f.write(f"{line}\n")
            
            print(f"  Created {split_file} with {len(filtered_lines)} images")
    
    print("\nDistribution completed!")

if __name__ == "__main__":
    # Get the dataset root directory (parent of scripts directory)
    root_dir = Path(__file__).parent.parent
    distribute_sets(root_dir)

