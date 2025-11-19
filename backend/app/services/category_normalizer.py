"""
Category Normalization Service
Maps various category names to consistent tags
"""

# Category mapping dictionary
CATEGORY_MAPPINGS = {
    # Women's categories
    "kurta": ["kurta", "kurtis", "kurti", "kurtas", "kurti set", "kurta set"],
    "shalwar_kameez": ["shalwar kameez", "shalwar kameez set", "suit", "suit set", "unstitched"],
    "saree": ["saree", "sari", "sarees", "saris"],
    "lehenga": ["lehenga", "lehenga choli", "lehenga set"],
    "dress": ["dress", "dresses", "frock", "gown"],
    "tops": ["top", "tops", "tunic", "tunics", "shirt", "shirts"],
    "trousers": ["trouser", "trousers", "pants", "pant", "pantaloons"],
    "dupatta": ["dupatta", "dupattas", "chunri", "chunris"],
    
    # Men's categories
    "shalwar_kameez_m": ["shalwar kameez", "suit", "suit set", "unstitched", "kurta pajama"],
    "kurta_m": ["kurta", "kurtas", "kurta set"],
    "shirt_m": ["shirt", "shirts", "formal shirt", "casual shirt"],
    "trouser_m": ["trouser", "trousers", "pants", "pant", "churidar"],
    "waistcoat": ["waistcoat", "waistcoats", "vest", "vests"],
    
    # Unisex/General
    "accessories": ["accessories", "accessory", "jewelry", "jewellery", "bag", "bags", "shoes", "footwear"],
}

# Reverse mapping for quick lookup
REVERSE_MAPPING = {}
for normalized, variants in CATEGORY_MAPPINGS.items():
    for variant in variants:
        REVERSE_MAPPING[variant.lower()] = normalized


def normalize_category(category_name: str, gender: str = None) -> str:
    """
    Normalize a category name to a consistent tag.
    
    Args:
        category_name: The category name from the website (e.g., "Kurtis", "Women → Stitched", "Shirts")
        gender: Optional gender prefix ('m' for men, 'w' for women)
    
    Returns:
        Normalized category tag
    """
    if not category_name:
        return "other"
    
    # Handle "Women → Stitched" or "Men → Eastern" format
    # Extract the part after the arrow if present
    if "→" in category_name or "->" in category_name:
        parts = category_name.split("→") if "→" in category_name else category_name.split("->")
        if len(parts) > 1:
            category_name = parts[1].strip()  # Use the part after arrow
        else:
            category_name = parts[0].strip()
    
    # Convert to lowercase and strip whitespace
    category_lower = category_name.lower().strip()
    
    # Check reverse mapping first
    if category_lower in REVERSE_MAPPING:
        normalized = REVERSE_MAPPING[category_lower]
        
        # Add gender suffix if needed
        if gender:
            if gender.lower() == 'm' and not normalized.endswith('_m'):
                # For men's categories, add _m suffix if not already present
                if normalized in ["shalwar_kameez", "kurta", "shirt", "trouser"]:
                    normalized = f"{normalized}_m"
        
        return normalized
    
    # If not found, try partial matching
    for normalized, variants in CATEGORY_MAPPINGS.items():
        for variant in variants:
            if variant in category_lower or category_lower in variant:
                if gender and gender.lower() == 'm':
                    if normalized in ["shalwar_kameez", "kurta", "shirt", "trouser"]:
                        return f"{normalized}_m"
                return normalized
    
    # Try to extract category from common words in the category name
    category_keywords = {
        'kurta': 'kurta',
        'kurti': 'kurta',
        'shirt': 'shirt_m' if gender == 'm' else 'tops',
        'shalwar': 'shalwar_kameez',
        'kameez': 'shalwar_kameez',
        'suit': 'shalwar_kameez',
        'dress': 'dress',
        'trouser': 'trouser_m' if gender == 'm' else 'trousers',
        'pant': 'trouser_m' if gender == 'm' else 'trousers',
        'saree': 'saree',
        'lehenga': 'lehenga',
    }
    
    for keyword, normalized_cat in category_keywords.items():
        if keyword in category_lower:
            if gender and gender.lower() == 'm' and normalized_cat in ["shalwar_kameez", "kurta", "shirt", "trouser"]:
                if not normalized_cat.endswith('_m'):
                    return f"{normalized_cat}_m"
            return normalized_cat
    
    # Default fallback
    return category_lower.replace(" ", "_").replace("-", "_")


def get_category_display_name(normalized_category: str) -> str:
    """
    Get a display-friendly name for a normalized category.
    
    Args:
        normalized_category: The normalized category tag
    
    Returns:
        Display name
    """
    display_names = {
        "kurta": "Kurta",
        "shalwar_kameez": "Shalwar Kameez",
        "saree": "Saree",
        "lehenga": "Lehenga",
        "dress": "Dress",
        "tops": "Tops",
        "trousers": "Trousers",
        "dupatta": "Dupatta",
        "shalwar_kameez_m": "Shalwar Kameez",
        "kurta_m": "Kurta",
        "shirt_m": "Shirt",
        "trouser_m": "Trousers",
        "waistcoat": "Waistcoat",
        "accessories": "Accessories",
    }
    
    return display_names.get(normalized_category, normalized_category.replace("_", " ").title())


def extract_gender_from_category(main_category: str) -> str:
    """
    Extract gender from main category string.
    
    Args:
        main_category: Main category like "Women → Stitched" or "Men → Eastern"
    
    Returns:
        'w' for women, 'm' for men, None if unknown
    """
    if not main_category:
        return None
    
    main_lower = main_category.lower()
    if "women" in main_lower or "woman" in main_lower:
        return "w"
    elif "men" in main_lower or "man" in main_lower:
        return "m"
    
    return None



