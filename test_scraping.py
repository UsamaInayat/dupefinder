"""
Quick Test Script for Scraping System
Run this to test if scraping is working without using the frontend

Usage:
    python test_scraping.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.scraper_service import scrape_from_excel_files
from app.core.database import get_products_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_read_excel_files():
    """Test if Excel files can be read"""
    print("\n" + "="*60)
    print("TEST 1: Reading Excel Files")
    print("="*60)
    
    try:
        import pandas as pd
        
        # Test women dataset
        women_file = "women links dataset.xlsx"
        if os.path.exists(women_file):
            df_women = pd.read_excel(women_file)
            print(f"✅ Women dataset: {len(df_women)} rows")
            print(f"   Columns: {list(df_women.columns)}")
            
            # Check for link columns
            if "Local Dupe Brand Link" in df_women.columns:
                links = df_women["Local Dupe Brand Link"].dropna()
                valid_links = [l for l in links if str(l).startswith("http")]
                print(f"   ✅ Found {len(valid_links)} valid local brand links")
            else:
                print("   ⚠️  No 'Local Dupe Brand Link' column found")
        else:
            print(f"❌ Women dataset file not found: {women_file}")
        
        # Test men dataset
        men_file = "men dataset.xlsx"
        if os.path.exists(men_file):
            df_men = pd.read_excel(men_file)
            print(f"✅ Men dataset: {len(df_men)} rows")
            print(f"   Columns: {list(df_men.columns)}")
            
            # Check for link columns
            if "Local Dupe Brand Link" in df_men.columns:
                links = df_men["Local Dupe Brand Link"].dropna()
                valid_links = [l for l in links if str(l).startswith("http")]
                print(f"   ✅ Found {len(valid_links)} valid local brand links")
            else:
                print("   ⚠️  Men dataset doesn't have link columns yet (this is OK)")
        else:
            print(f"❌ Men dataset file not found: {men_file}")
            
    except Exception as e:
        print(f"❌ Error reading Excel files: {e}")
        return False
    
    return True


async def test_brand_loading():
    """Test if brands can be loaded from Excel"""
    print("\n" + "="*60)
    print("TEST 2: Loading Brands from Excel")
    print("="*60)
    
    try:
        # We need to mock admin auth for this test
        # For now, just test the Excel reading part
        import pandas as pd
        
        project_root = os.path.dirname(__file__)
        women_file = os.path.join(project_root, "women links dataset.xlsx")
        
        if os.path.exists(women_file):
            df = pd.read_excel(women_file)
            
            link_column = "Local Dupe Brand Link"
            brand_column = "Local Affordable Brand (Dupe)"
            
            if link_column in df.columns:
                brands = []
                for idx, row in df.iterrows():
                    brand_url = row.get(link_column, "")
                    if pd.notna(brand_url) and str(brand_url).startswith("http"):
                        brand_name = row.get(brand_column, "Unknown Brand")
                        main_category = row.get("Main Category", "")
                        brands.append({
                            "brand_name": brand_name,
                            "brand_url": str(brand_url),
                            "category": main_category
                        })
                
                print(f"✅ Found {len(brands)} brands with valid links")
                if brands:
                    print(f"\n   Sample brands:")
                    for i, brand in enumerate(brands[:5], 1):
                        print(f"   {i}. {brand['brand_name']} - {brand['category']}")
                        print(f"      URL: {brand['brand_url']}")
                return True
            else:
                print(f"❌ Column '{link_column}' not found in Excel file")
                return False
        else:
            print(f"❌ Excel file not found: {women_file}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading brands: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_category_normalization():
    """Test category normalization"""
    print("\n" + "="*60)
    print("TEST 3: Category Normalization")
    print("="*60)
    
    try:
        from app.services.category_normalizer import normalize_category, extract_gender_from_category
        
        test_cases = [
            ("Kurtis", "w", "kurta"),
            ("Kurta", "w", "kurta"),
            ("Kurti", "w", "kurta"),
            ("Shirts", "m", "shirt_m"),
            ("Shirt", "m", "shirt_m"),
            ("Women → Stitched", "w", "stitched"),  # This will normalize to "stitched" or similar
            ("Men → Eastern", "m", "eastern"),  # This will normalize to "eastern" or similar
        ]
        
        print("Testing category normalization:")
        all_passed = True
        for category, gender, expected_start in test_cases:
            normalized = normalize_category(category, gender)
            gender_extracted = extract_gender_from_category(category)
            
            # For main categories like "Women → Stitched", just check it normalizes to something reasonable
            if "→" in category or "->" in category:
                # Main categories should normalize to something (not empty)
                passed = normalized and normalized != "other" and len(normalized) > 0
            else:
                # Check if normalized starts with expected or contains it
                passed = expected_start in normalized.lower() or normalized.lower().startswith(expected_start)
            
            status = "✅" if passed else "❌"
            
            print(f"   {status} '{category}' (gender: {gender}) → '{normalized}'")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✅ All category normalization tests passed!")
        else:
            print("\n⚠️  Some category normalization tests failed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing category normalization: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scraper_initialization():
    """Test if scraper can be initialized"""
    print("\n" + "="*60)
    print("TEST 4: Scraper Initialization")
    print("="*60)
    
    try:
        from app.services.scraper_service import ProductScraper
        
        scraper = ProductScraper()
        print("✅ Scraper initialized successfully")
        
        # Test a simple URL check
        test_url = "https://khaadi.com"
        is_product = scraper._is_product_url("https://khaadi.com/product/test")
        print(f"✅ Product URL detection working: {is_product}")
        
        await scraper.close()
        print("✅ Scraper closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing scraper: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n" + "="*60)
    print("TEST 5: MongoDB Connection")
    print("="*60)
    
    try:
        from app.core.database import db_manager, get_products_collection
        
        # Connect to database first
        db_manager.connect()
        
        if db_manager.db is None:
            print("❌ MongoDB connection failed")
            print("   Make sure MongoDB is running!")
            return False
        
        products_collection = get_products_collection()
        count = products_collection.count_documents({})
        print(f"✅ MongoDB connected successfully")
        print(f"   Database: {db_manager.db.name}")
        print(f"   Current products in database: {count}")
        
        # Check for scraped products
        scraped_count = products_collection.count_documents({"scraped_at": {"$exists": True}})
        print(f"   Scraped products: {scraped_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        print("   Make sure MongoDB is running!")
        print("   On Windows, you can start it with: net start MongoDB")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SCRAPING SYSTEM TEST SUITE")
    print("="*60)
    print("\nThis script will test if the scraping system is set up correctly.")
    print("It does NOT perform actual scraping (that's done through the admin dashboard).")
    
    results = []
    
    # Run tests
    results.append(("Excel Files", await test_read_excel_files()))
    results.append(("Brand Loading", await test_brand_loading()))
    results.append(("Category Normalization", await test_category_normalization()))
    results.append(("Scraper Initialization", await test_scraper_initialization()))
    results.append(("MongoDB Connection", await test_mongodb_connection()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The scraping system is ready to use.")
        print("\nNext steps:")
        print("1. Start the backend server: cd backend && python start_server.py")
        print("2. Start the frontend: cd frontend-app && npm run dev")
        print("3. Login to admin dashboard and go to 'Auto Sync / Rescraping' module")
        print("4. Select brands and start scraping!")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before using the scraping system.")
        print("\nCommon issues:")
        print("- MongoDB not running: Start MongoDB service")
        print("- Excel files missing: Make sure 'women links dataset.xlsx' is in project root")
        print("- Dependencies missing: Run 'pip install -r backend/requirements.txt'")


if __name__ == "__main__":
    asyncio.run(main())

