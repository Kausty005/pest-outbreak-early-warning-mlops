import os
import json
import random
import time
from PIL import Image

def generate_unique_id():
    """Generate unique ID: 7 random digits + 3 timestamp digits"""
    random_part = random.randint(1000000, 9999999)
    timestamp_part = int(time.time()) % 1000
    return int(f"{random_part}{timestamp_part:03d}")

def get_image_info(image_path):
    """Get image information using PIL"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            file_size = os.path.getsize(image_path)
            return width, height, file_size
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return 512, 512, 0

def generate_coco_annotation(image_path, category_name, category_id):
    """Generate COCO format annotation for a single image"""
    # Generate unique IDs
    image_id = generate_unique_id()
    annotation_id = generate_unique_id()
    
    # Get image information
    width, height, file_size = get_image_info(image_path)
    
    # Get file extension
    _, ext = os.path.splitext(image_path)
    format_type = ext.upper().replace('.', '')
    
    # Create COCO format annotation
    coco_data = {
        "info": {
            "description": "data",
            "version": "1.0",
            "year": 2025,
            "contributor": "search engine",
            "source": "augmented",
            "license": {
                "name": "Creative Commons Attribution 4.0 International",
                "url": "https://creativecommons.org/licenses/by/4.0/"
            }
        },
        "images": [
            {
                "id": image_id,
                "width": width,
                "height": height,
                "file_name": os.path.basename(image_path),
                "size": file_size,
                "format": format_type,
                "url": "",
                "hash": "",
                "status": "success"
            }
        ],
        "annotations": [
            {
                "id": annotation_id,
                "image_id": image_id,
                "category_id": category_id,
                "segmentation": [],
                "area": width * height,
                "bbox": [0, 0, width, height]
            }
        ],
        "categories": [
            {
                "id": category_id,
                "name": category_name,
                "supercategory": "corn"
            }
        ]
    }
    
    return coco_data

def process_directory(directory_path, category_name, category_id):
    """Process all images in a directory and generate COCO annotations"""
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    image_files = []
    
    for file in os.listdir(directory_path):
        if any(file.lower().endswith(ext.lower()) for ext in image_extensions):
            image_files.append(file)
    
    print(f"Found {len(image_files)} images in {directory_path}")
    
    # Generate COCO annotation for each image
    for image_file in image_files:
        image_path = os.path.join(directory_path, image_file)
        
        # Generate COCO data
        coco_data = generate_coco_annotation(image_path, category_name, category_id)
        
        # Create JSON filename (same as image name but with .json extension)
        json_filename = os.path.splitext(image_file)[0] + '.json'
        json_path = os.path.join(directory_path, json_filename)
        
        # Save JSON file
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(coco_data, f, indent=2, ensure_ascii=False)
            print(f"Generated: {json_filename}")
        except Exception as e:
            print(f"Error saving {json_filename}: {e}")

def main():
    """Main function to process all directories"""
    # Define category mappings
    categories = {
        "Healthy": 1,
        "Gray_Leaf_Spot": 2,
        "Common_Rust": 3,
        "Blight": 4
    }
    
    # Process each directory
    for category_name, category_id in categories.items():
        print(f"\nProcessing {category_name}...")
        process_directory(category_name, category_name, category_id)
    
    print("\nAll COCO annotations generated successfully!")

if __name__ == "__main__":
    main() 