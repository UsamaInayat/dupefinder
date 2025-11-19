# DupeFinder Product Dataset

## Overview

This directory contains the sample product catalog for the DupeFinder project (40% milestone demo).

**Total Products**: 100
**Created**: 2025-11-08 22:45:53

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
print(f"Loaded {len(catalog)} products")

# Filter by category
bags = catalog[catalog['category'] == 'bags']
print(f"Found {len(bags)} bags")
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

