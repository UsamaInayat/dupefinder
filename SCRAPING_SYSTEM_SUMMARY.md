# Product Scraping System - Implementation Summary

## Overview

A comprehensive web scraping system has been built to scrape product catalogues from brand websites listed in Excel files (`men dataset.xlsx` and `women links dataset.xlsx`). The system normalizes category tags and stores products in MongoDB with consistent categorization.

## Key Features

### 1. **Category Normalization** ✅
- **File**: `backend/app/services/category_normalizer.py`
- Maps various category names to consistent tags
- Examples:
  - "kurta", "kurtis", "kurti" → all become `"kurta"`
  - "shalwar kameez", "suit", "suit set" → all become `"shalwar_kameez"`
  - Handles gender-specific categories (men's vs women's)
- Provides display names for normalized categories

### 2. **Web Scraping Service** ✅
- **File**: `backend/app/services/scraper_service.py`
- Scrapes products from brand websites
- Extracts:
  - Product name
  - Price
  - Image URL
  - Description
  - Category (normalized)
- Handles multiple brand websites generically
- Stores products in MongoDB with normalized categories

### 3. **Admin Dashboard Integration** ✅
- **Module**: Auto Sync / Rescraping
- Reads brands from Excel files
- Allows selecting multiple brands for scraping
- Real-time progress tracking
- Shows products added per brand
- Activity logs

## Excel File Structure

### Women Links Dataset (`women links dataset.xlsx`)
- **Columns**:
  - `Main Category`: e.g., "Women → Stitched"
  - `Luxury / International Brand`: e.g., "Gucci", "Dior"
  - `Pakistani Luxury / Designer Brand`: e.g., "Élan", "HSY"
  - `Local Affordable Brand (Dupe)`: e.g., "Khaadi", "Sapphire"
  - `Luxury Brand Link`: URL to luxury brand website
  - `Pakistani Designer Brand Link`: URL to Pakistani designer website
  - `Local Dupe Brand Link`: URL to affordable brand website
  - Price ranges for each category

### Men Dataset (`men dataset.xlsx`)
- Similar structure (may not have links yet)

## How It Works

### 1. **Reading Brands from Excel**
```python
# Backend reads Excel files from project root
women_file = "women links dataset.xlsx"
df = pd.read_excel(women_file)

# Extracts brand URLs based on type (luxury/pakistani/local)
# Returns list of brands with URLs and categories
```

### 2. **Scraping Process**
```python
# For each selected brand:
1. Visit brand website
2. Find product listing pages
3. Extract product information:
   - Name, price, image, description
4. Normalize category tag
5. Store in MongoDB
```

### 3. **Category Normalization**
```python
# Example:
Website category: "Kurtis" → Normalized: "kurta"
Website category: "Shirts" → Normalized: "shirt_m" (for men)
Website category: "Shalwar Kameez Set" → Normalized: "shalwar_kameez"
```

### 4. **Storage in MongoDB**
```javascript
{
  name: "Embroidered Kurta",
  brand: "Khaadi",
  category: "Women → Stitched",
  normalized_category: "kurta",  // Consistent tag!
  price: 5000,
  image_url: "https://...",
  product_url: "https://...",
  gender: "w",
  scraped_at: ISODate("..."),
  broken_link: false
}
```

## API Endpoints

### Get Available Brands
```
GET /api/admin/scraping/brands?brand_type=local
```
Returns brands from Excel files with:
- Brand name
- Brand URL
- Category
- Current product count in database

### Start Scraping
```
POST /api/admin/scraping/start
Body: {
  "brand_ids": [
    {
      "brand_name": "Khaadi",
      "brand_url": "https://khaadi.com",
      "category": "Women → Stitched"
    }
  ]
}
```

### Check Scraping Status
```
GET /api/admin/scraping/status/{job_id}
```
Returns:
- Progress (brands completed, products added)
- Status (running/completed/failed)
- Activity logs

### Get Scraping History
```
GET /api/admin/scraping/history?limit=5
```

## Frontend Integration

### Auto Sync Module
- Displays brands from Excel files
- Multi-select checkboxes for brands
- Shows category and product count
- Real-time progress tracking
- Activity logs display

## Category Consistency

### Problem Solved
Different websites use different category names:
- Site A: "Kurta"
- Site B: "Kurtis"
- Site C: "Kurti Set"

### Solution
All normalized to: `"kurta"`

When user searches for "kurta", they see products from ALL sites, regardless of how the original site categorized them.

## Files Created/Modified

### New Files:
1. `backend/app/services/category_normalizer.py` - Category mapping
2. `backend/app/services/scraper_service.py` - Web scraping logic

### Modified Files:
1. `backend/app/api/routes/admin_new.py` - Scraping endpoints
2. `backend/requirements.txt` - Added beautifulsoup4, lxml, openpyxl, pandas
3. `frontend-app/src/components/admin/ScrapingManagement.jsx` - Updated to handle brand objects

## Dependencies Added

```txt
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0             # XML/HTML parser
openpyxl>=3.1.0         # Excel file reading
pandas>=2.1.0           # Data manipulation
```

## Installation

```bash
cd backend
pip install beautifulsoup4 lxml openpyxl pandas
```

## Usage

1. **Place Excel files in project root**:
   - `women links dataset.xlsx`
   - `men dataset.xlsx`

2. **Start backend server**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Access Admin Dashboard** → Auto Sync module

4. **Select brands** from the list (read from Excel)

5. **Click "Start Scraping"**

6. **Monitor progress** in real-time

7. **Products stored** in MongoDB with normalized categories

## Next Steps

1. **Customize scrapers** for specific websites (some sites may need custom logic)
2. **Add more category mappings** as needed
3. **Implement retry logic** for failed scrapes
4. **Add rate limiting** to respect website policies
5. **Track last scrape time** per brand
6. **Add image validation** (check if image URLs are valid)

## Notes

- Generic scraper works for most sites but may need customization for specific websites
- Scraping respects robots.txt and adds delays between requests
- Products are deduplicated by `product_url`
- Categories are normalized automatically during scraping

---

**Status**: ✅ Complete and Ready for Testing
**Date**: November 11, 2025

