"""
DupeFinder ML Engine - Product Dataset Creator
Task 2.5: Create sample product dataset (50-100 items)

This script creates a sample product catalog with fashion items:
- Downloads or generates fashion product images
- Organizes by category (bags, shoes, watches, clothing, accessories)
- Creates metadata CSV file
- Prepares for embedding generation
"""

import sys
from pathlib import Path
import csv
import time
from PIL import Image, ImageDraw, ImageFont
import random


def create_product_directories():
    """Create directory structure for product catalog"""
    print("=" * 60)
    print("STEP 1: Creating Product Directory Structure")
    print("=" * 60)
    
    base_dir = Path("data/products")
    categories = ['bags', 'shoes', 'watches', 'clothing', 'accessories']
    
    for category in categories:
        category_dir = base_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {category_dir}")
    
    print(f"\n[SUCCESS] Directory structure created in {base_dir}\n")
    return base_dir, categories


def generate_sample_product_image(
    product_name: str,
    category: str,
    size: tuple = (800, 800)
) -> Image.Image:
    """
    Generate a sample product image with text overlay.
    
    In a real scenario, these would be actual product photos.
    For the demo, we create colored images with product information.
    """
    # Category colors (different color per category)
    category_colors = {
        'bags': (139, 69, 19),      # Brown
        'shoes': (70, 130, 180),    # Steel Blue
        'watches': (169, 169, 169),  # Dark Gray
        'clothing': (219, 112, 147), # Pale Violet Red
        'accessories': (184, 134, 11) # Dark Goldenrod
    }
    
    base_color = category_colors.get(category, (128, 128, 128))
    
    # Add some variation
    color = tuple(
        min(255, max(0, c + random.randint(-30, 30)))
        for c in base_color
    )
    
    # Create image
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    text_lines = [
        category.upper(),
        "",
        product_name,
        "",
        f"Demo Product",
        "DupeFinder"
    ]
    
    # Try to use a font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw text
    y_position = size[1] // 4
    for i, line in enumerate(text_lines):
        font = font_large if i == 0 else font_small
        
        # Get text size for centering
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x_position = (size[0] - text_width) // 2
        
        draw.text((x_position, y_position), line, fill='white', font=font)
        y_position += 80
    
    return img


def create_sample_products(base_dir: Path, categories: list, num_per_category: int = 20):
    """Create sample product images and metadata"""
    print("=" * 60)
    print("STEP 2: Creating Sample Product Images")
    print("=" * 60)
    print(f"Generating {num_per_category} products per category...")
    print()
    
    products = []
    product_id = 1
    
    # Brand names
    brands = ['StyleCo', 'FashionHub', 'TrendyWear', 'UrbanStyle', 'ChicBoutique',
              'ModernLook', 'ClassicWear', 'ElegantStyle', 'CasualVibes', 'LuxeLine']
    
    # Price ranges by category
    price_ranges = {
        'bags': (30, 200),
        'shoes': (40, 180),
        'watches': (50, 300),
        'clothing': (20, 150),
        'accessories': (10, 100)
    }
    
    for category in categories:
        print(f"Creating {category}...")
        category_dir = base_dir / category
        
        for i in range(num_per_category):
            # Generate product name
            product_name = f"{category.capitalize()[:-1]} {chr(65 + i)}"
            
            # Generate random price
            price_min, price_max = price_ranges[category]
            price = random.randint(price_min, price_max)
            
            # Random brand
            brand = random.choice(brands)
            
            # Create image
            img = generate_sample_product_image(product_name, category)
            
            # Save image
            image_filename = f"{category}_{product_id:03d}.jpg"
            image_path = category_dir / image_filename
            img.save(image_path, 'JPEG', quality=85)
            
            # Store metadata
            products.append({
                'id': product_id,
                'name': product_name,
                'category': category,
                'brand': brand,
                'price': price,
                'image_path': str(image_path.relative_to(base_dir.parent)),
                'description': f"Stylish {product_name} from {brand}"
            })
            
            product_id += 1
        
        print(f"  [OK] Created {num_per_category} {category}")
    
    print(f"\n[SUCCESS] Created {len(products)} product images!\n")
    return products


def save_product_metadata(products: list, base_dir: Path):
    """Save product metadata to CSV file"""
    print("=" * 60)
    print("STEP 3: Saving Product Metadata")
    print("=" * 60)
    
    metadata_file = base_dir.parent / "product_catalog.csv"
    
    # Write CSV
    with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'name', 'category', 'brand', 'price', 'image_path', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for product in products:
            writer.writerow(product)
    
    print(f"[OK] Metadata saved to: {metadata_file}")
    print(f"     Total products: {len(products)}")
    print(f"     Columns: {', '.join(fieldnames)}")
    
    # Print summary
    from collections import Counter
    category_counts = Counter(p['category'] for p in products)
    print(f"\n     Category distribution:")
    for category, count in category_counts.items():
        print(f"       - {category}: {count} items")
    
    print(f"\n[SUCCESS] Metadata saved successfully!\n")
    return metadata_file


def create_readme(base_dir: Path, num_products: int):
    """Create README file explaining the dataset"""
    print("=" * 60)
    print("STEP 4: Creating Dataset Documentation")
    print("=" * 60)
    
    readme_path = base_dir.parent / "DATASET_README.md"
    
    readme_content = f"""# DupeFinder Product Dataset

## Overview

This directory contains the sample product catalog for the DupeFinder project (40% milestone demo).

**Total Products**: {num_products}
**Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Structure

```
data/
├── products/
│   ├── bags/           # Bag product images
│   ├── shoes/          # Shoe product images
│   ├── watches/        # Watch product images
│   ├── clothing/       # Clothing product images
│   └── accessories/    # Accessory product images
├── product_catalog.csv # Product metadata (names, prices, categories, etc.)
└── DATASET_README.md   # This file
```

## Categories

1. **Bags** - Handbags, backpacks, purses, totes
2. **Shoes** - Sneakers, boots, heels, sandals
3. **Watches** - Wristwatches, smartwatches, luxury watches
4. **Clothing** - Shirts, dresses, jackets, pants
5. **Accessories** - Jewelry, scarves, belts, sunglasses

## Product Metadata

The `product_catalog.csv` file contains:
- **id**: Unique product identifier
- **name**: Product name
- **category**: Product category
- **brand**: Brand name
- **price**: Price in USD
- **image_path**: Relative path to product image
- **description**: Product description

## Usage

### Load Product Catalog

```python
import pandas as pd

# Load metadata
catalog = pd.read_csv('data/product_catalog.csv')
print(f"Loaded {{len(catalog)}} products")

# Filter by category
bags = catalog[catalog['category'] == 'bags']
print(f"Found {{len(bags)}} bags")
```

### Extract Embeddings

```python
from embeddings.feature_extractor import FeatureExtractor

# Initialize extractor
extractor = FeatureExtractor()

# Extract embeddings for all products
image_paths = catalog['image_path'].tolist()
embeddings = extractor.extract_batch(image_paths, batch_size=32)

# Save embeddings
extractor.extract_and_save(
    image_paths,
    'data/embeddings/product_embeddings.pkl',
    save_metadata=True
)
```

## Notes

- **Demo Dataset**: These are synthetic product images created for the 40% milestone demo
- **Real Dataset**: For production (60-100% milestone), replace with actual product photos
- **Image Quality**: All images are 800x800 pixels, JPEG format
- **Licensing**: Demo images only, not for commercial use

## Next Steps

1. Run embedding extraction: `python ml-engine/precompute_embeddings.py`
2. Test similarity search with these products
3. Replace with real product images for final demo

"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"[OK] Documentation created: {readme_path}")
    print(f"\n[SUCCESS] Dataset documentation complete!\n")
    return readme_path


def display_summary(base_dir: Path, products: list, metadata_file: Path):
    """Display final summary"""
    print("=" * 60)
    print("FINAL SUMMARY - Product Dataset Created")
    print("=" * 60)
    
    print(f"\n[OK] Created {len(products)} sample products")
    print(f"[OK] 5 categories (20 products each)")
    print(f"[OK] Product images saved in: {base_dir}")
    print(f"[OK] Metadata saved in: {metadata_file}")
    print(f"[OK] Dataset ready for embedding extraction")
    
    print(f"\n[FILES] Files Created:")
    print(f"   - Product images: {len(products)} JPG files")
    print(f"   - Metadata: product_catalog.csv")
    print(f"   - Documentation: DATASET_README.md")
    
    print(f"\n[STATS] Dataset Statistics:")
    print(f"   - Total products: {len(products)}")
    print(f"   - Categories: 5")
    print(f"   - Products per category: 20")
    print(f"   - Image size: 800x800 pixels")
    
    total_size_mb = sum(
        (base_dir / p['image_path'].replace('data/products/', '')).stat().st_size
        for p in products if (base_dir / p['image_path'].replace('data/products/', '')).exists()
    ) / (1024 * 1024)
    print(f"   - Total dataset size: {total_size_mb:.2f} MB")
    
    print(f"\n[NEXT] Next Steps:")
    print(f"   1. Run: python ml-engine/precompute_embeddings.py")
    print(f"   2. This will generate embeddings for all products")
    print(f"   3. Then you can test similarity search!")
    
    print("\n" + "=" * 60)


def main():
    """Create the sample product dataset"""
    print("\n" + "=" * 60)
    print("DupeFinder ML Engine - Product Dataset Creator")
    print("Task 2.5: Creating Sample Product Catalog")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    # Step 1: Create directories
    base_dir, categories = create_product_directories()
    
    # Step 2: Create sample products (20 per category = 100 total)
    products = create_sample_products(base_dir, categories, num_per_category=20)
    
    # Step 3: Save metadata
    metadata_file = save_product_metadata(products, base_dir)
    
    # Step 4: Create documentation
    readme_file = create_readme(base_dir, len(products))
    
    # Display summary
    display_summary(base_dir, products, metadata_file)
    
    total_time = time.time() - start_time
    
    print(f"\n[TIME] Total time: {total_time:.2f} seconds")
    print(f"\n[COMPLETE] Task 2.5 Complete: Product dataset created!")
    print(f"You can now proceed to Task 2.6: Pre-compute Embeddings\n")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

