"""
Web Scraping Service for Product Catalogues
Scrapes products from brand websites and stores in MongoDB with normalized categories
"""

import pandas as pd
import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging

from app.core.database import get_products_collection
from app.services.category_normalizer import normalize_category, extract_gender_from_category

logger = logging.getLogger(__name__)


class ProductScraper:
    """Scrapes products from brand websites"""
    
    def __init__(self):
        # Reduced timeout to prevent hanging
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self.scraped_count = 0
        self.failed_count = 0
        self.errors = []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def scrape_brand_website(self, brand_url: str, brand_name: str, 
                                   main_category: str, price_range: str = None) -> List[Dict]:
        """
        Scrape products from a brand website.
        
        Args:
            brand_url: Base URL of the brand website
            brand_name: Name of the brand
            main_category: Main category from dataset
            price_range: Price range if available
        
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            # Extract gender from main category
            gender = extract_gender_from_category(main_category)
            
            logger.info(f"Scraping brand: {brand_name} from {brand_url}")
            
            # Try to find product listing pages
            product_urls = await self._find_product_pages(brand_url)
            
            logger.info(f"Found {len(product_urls)} product URLs for {brand_name}")
            
            if not product_urls:
                logger.warning(f"No product URLs found for {brand_name} at {brand_url}")
                return products
            
            for product_url in product_urls[:50]:  # Limit to 50 products per brand
                try:
                    product = await self._scrape_product_page(
                        product_url, brand_name, main_category, gender, price_range
                    )
                    if product:
                        products.append(product)
                        self.scraped_count += 1
                except Exception as e:
                    logger.error(f"Error scraping product {product_url}: {e}")
                    self.failed_count += 1
                    self.errors.append(f"{product_url}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scraping brand {brand_url}: {e}")
            self.errors.append(f"{brand_url}: {str(e)}")
        
        return products
    
    async def _find_product_pages(self, base_url: str) -> List[str]:
        """
        Find product listing pages on the website.
        This is a generic approach - may need customization per site.
        """
        product_urls = []
        
        logger.info(f"Finding product pages for {base_url}")
        
        try:
            # Common product listing page patterns
            common_paths = [
                "/products",
                "/shop",
                "/catalog",
                "/collection",
                "/category",
                "/women",
                "/men",
                "/pret",
                "/unstitched",
            ]
            
            for path in common_paths:
                try:
                    url = urljoin(base_url, path)
                    response = await self.client.get(url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find product links (common patterns)
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            full_url = urljoin(url, href)
                            
                            # Check if it looks like a product page
                            if self._is_product_url(full_url):
                                if full_url not in product_urls:
                                    product_urls.append(full_url)
                        
                        if product_urls:
                            logger.info(f"Found {len(product_urls)} product URLs from {url}")
                            break  # Found products, stop searching
                
                except Exception as e:
                    logger.debug(f"Error checking {url}: {e}")
                    continue
            
            # If no products found, try scraping homepage for product links
            if not product_urls:
                logger.info(f"No products found in common paths, trying homepage: {base_url}")
                try:
                    response = await self.client.get(base_url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        links = soup.find_all('a', href=True)
                        logger.info(f"Found {len(links)} links on homepage")
                        for link in links:
                            href = link.get('href', '')
                            full_url = urljoin(base_url, href)
                            if self._is_product_url(full_url):
                                if full_url not in product_urls:
                                    product_urls.append(full_url)
                        logger.info(f"Found {len(product_urls)} product URLs from homepage")
                except Exception as e:
                    logger.warning(f"Error scraping homepage: {e}")
                    pass
        
        except Exception as e:
            logger.error(f"Error finding product pages for {base_url}: {e}")
        
        logger.info(f"Total product URLs found for {base_url}: {len(product_urls)}")
        return product_urls[:20]  # Limit to 20 products per brand for now
    
    def _is_product_url(self, url: str) -> bool:
        """Check if URL looks like a product page"""
        url_lower = url.lower()
        product_indicators = ['/product/', '/item/', '/p/', '/dp/', '/-p-', '/products/']
        exclude_patterns = ['/category/', '/collection/', '/shop/', '/cart/', '/checkout/', '/search', '/filter', '/page=', '/tag=']
        
        # Check if it has product indicators
        has_product_indicator = any(ind in url_lower for ind in product_indicators)
        
        # Check if it doesn't have exclude patterns
        has_exclude = any(pattern in url_lower for pattern in exclude_patterns)
        
        # Also check if URL has a product-like structure (has multiple path segments)
        # Many e-commerce sites use patterns like /category/product-name or /brand/product-name
        url_parts = [p for p in url_lower.split('/') if p and p not in ['http:', 'https:', 'www.', '']]
        has_product_structure = len(url_parts) >= 2  # At least category/product or brand/product
        
        # Accept if it has product indicator OR has product structure (and not excluded)
        return (has_product_indicator or has_product_structure) and not has_exclude
    
    async def _scrape_product_page(self, product_url: str, brand_name: str,
                                  main_category: str, gender: Optional[str],
                                  price_range: str = None) -> Optional[Dict]:
        """
        Scrape a single product page.
        
        This is a generic scraper - may need customization per website.
        """
        try:
            response = await self.client.get(product_url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product category from the page (e.g., "Kurtis", "Shirts", "Kurta")
            product_category = self._extract_product_category(soup, product_url)
            
            # Use product category if found, otherwise use main category
            category_to_normalize = product_category if product_category else main_category
            
            # Extract product information (generic approach)
            product = {
                'name': self._extract_product_name(soup),
                'brand': brand_name,
                'category': main_category,  # Keep original main category
                'product_category': product_category,  # Category from website
                'normalized_category': normalize_category(category_to_normalize, gender),
                'price': self._extract_price(soup, price_range),
                'image_url': self._extract_image_url(soup, product_url),
                'product_url': product_url,
                'description': self._extract_description(soup),
                'scraped_at': datetime.utcnow(),
                'gender': gender,
                'broken_link': False,
            }
            
            # Validate product has minimum required fields
            if product['name'] and product['image_url']:
                return product
            
            return None
        
        except Exception as e:
            logger.error(f"Error scraping product page {product_url}: {e}")
            return None
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name from page"""
        # Try common selectors
        selectors = [
            'h1.product-title',
            'h1.product-name',
            'h1[itemprop="name"]',
            '.product-title',
            '.product-name',
            'h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown Product"
    
    def _extract_price(self, soup: BeautifulSoup, price_range: str = None) -> Optional[float]:
        """Extract product price from page"""
        # Try common price selectors
        selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.amount',
            '.cost',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numbers
                numbers = re.findall(r'[\d,]+', price_text.replace(',', ''))
                if numbers:
                    try:
                        return float(numbers[0])
                    except:
                        pass
        
        # If no price found, try to extract from price_range
        if price_range:
            numbers = re.findall(r'[\d,]+', price_range.replace(',', ''))
            if numbers:
                try:
                    return float(numbers[0])  # Use minimum price
                except:
                    pass
        
        return None
    
    def _extract_image_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract product image URL"""
        # Try common image selectors
        selectors = [
            'img.product-image',
            'img[itemprop="image"]',
            '.product-image img',
            '.product-gallery img',
            'meta[property="og:image"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                img_url = element.get('src') or element.get('content')
                if img_url:
                    return urljoin(base_url, img_url)
        
        # Fallback: find first large image
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src and ('product' in src.lower() or 'item' in src.lower()):
                return urljoin(base_url, src)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        selectors = [
            '.product-description',
            '[itemprop="description"]',
            '.description',
            '.product-details',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)[:500]  # Limit to 500 chars
        
        return ""
    
    def _extract_product_category(self, soup: BeautifulSoup, product_url: str) -> str:
        """
        Extract product category from the product page.
        This looks for category breadcrumbs, tags, or category links on the page.
        """
        # Try common category selectors
        category_selectors = [
            '.product-category',
            '.category',
            '[itemprop="category"]',
            '.breadcrumb a',
            '.product-tags a',
            '.product-collection',
            'nav[aria-label="Breadcrumb"] a',
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for element in elements:
                category_text = element.get_text(strip=True)
                # Skip common navigation words
                if category_text and category_text.lower() not in ['home', 'shop', 'products', 'all', 'main']:
                    # Check if it's a meaningful category (not just navigation)
                    if len(category_text) > 2 and category_text.lower() not in ['women', 'men', 'w', 'm']:
                        return category_text
        
        # Try to extract from URL path
        url_parts = product_url.lower().split('/')
        category_keywords = ['kurta', 'kurti', 'shirt', 'shalwar', 'kameez', 'suit', 'dress', 'trouser', 'pant']
        for part in url_parts:
            for keyword in category_keywords:
                if keyword in part:
                    return part.replace('-', ' ').title()
        
        return ""


async def scrape_from_excel_files(men_file: str = "men dataset.xlsx",
                                  women_file: str = "women links dataset.xlsx",
                                  brand_type: str = "local") -> Dict:
    """
    Scrape products from Excel files containing brand links.
    
    Args:
        men_file: Path to men's dataset Excel file
        women_file: Path to women's links dataset Excel file
        brand_type: Type of brand to scrape ('luxury', 'pakistani', 'local')
    
    Returns:
        Dictionary with scraping results
    """
    scraper = ProductScraper()
    products_collection = get_products_collection()
    
    all_products = []
    
    try:
        # Read women's dataset
        if women_file:
            try:
                df_women = pd.read_excel(women_file)
                logger.info(f"Read {len(df_women)} rows from women dataset")
                
                # Determine which link column to use
                link_column = None
                if brand_type == "luxury":
                    link_column = "Luxury Brand Link"
                elif brand_type == "pakistani":
                    link_column = "Pakistani Designer Brand Link"
                else:  # local
                    link_column = "Local Dupe Brand Link"
                
                if link_column in df_women.columns:
                    for idx, row in df_women.iterrows():
                        brand_url = row.get(link_column, "")
                        if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                            # Get brand name based on brand_type
                            if brand_type == "luxury":
                                brand_name = row.get("Luxury / International Brand", "Unknown Brand")
                                price_range = row.get("Luxury_Price_Range(PKR)", "")
                            elif brand_type == "pakistani":
                                brand_name = row.get("Pakistani Luxury / Designer Brand", "Unknown Brand")
                                price_range = row.get("Local_Price_Range(PKR)", "")  # Pakistani uses local price range
                            else:  # local
                                brand_name = row.get("Local Affordable Brand (Dupe)", "Unknown Brand")
                                price_range = row.get("Local_Price_Range(PKR)", "")
                            
                            main_category = row.get("Main Category", "")
                            
                            logger.info(f"Scraping {brand_name} from {brand_url} (Category: {main_category})")
                            products = await scraper.scrape_brand_website(
                                brand_url, brand_name, main_category, price_range
                            )
                            all_products.extend(products)
                            
                            # Small delay to avoid overwhelming servers
                            await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error reading women dataset: {e}")
                scraper.errors.append(f"Women dataset error: {str(e)}")
        
        # Read men's dataset (check if it has link columns)
        if men_file:
            try:
                df_men = pd.read_excel(men_file)
                logger.info(f"Read {len(df_men)} rows from men dataset")
                
                # Check if men dataset has link columns
                men_link_column = None
                men_brand_column = None
                if brand_type == "luxury":
                    men_link_column = "Luxury Brand Link" if "Luxury Brand Link" in df_men.columns else None
                    men_brand_column = "Luxury / International Brand"
                elif brand_type == "pakistani":
                    men_link_column = "Pakistani Designer Brand Link" if "Pakistani Designer Brand Link" in df_men.columns else None
                    men_brand_column = "Pakistani Luxury / Designer Brand"
                else:  # local
                    men_link_column = "Local Dupe Brand Link" if "Local Dupe Brand Link" in df_men.columns else None
                    men_brand_column = "Local Affordable Brand (Dupe)"
                
                # If men dataset has links, scrape them
                if men_link_column and men_link_column in df_men.columns:
                    for idx, row in df_men.iterrows():
                        brand_url = row.get(men_link_column, "")
                        if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                            brand_name = row.get(men_brand_column, "Unknown Brand")
                            main_category = row.get("Main Category", "")
                            
                            if brand_type == "luxury":
                                price_range = row.get("Luxury_Price_Range(PKR)", "")
                            else:
                                price_range = row.get("Local_Price_Range(PKR)", "")
                            
                            logger.info(f"Scraping {brand_name} from {brand_url} (Category: {main_category})")
                            products = await scraper.scrape_brand_website(
                                brand_url, brand_name, main_category, price_range
                            )
                            all_products.extend(products)
                            
                            # Small delay to avoid overwhelming servers
                            await asyncio.sleep(2)
                else:
                    logger.info("Men dataset does not have link columns yet. Skipping men's brands.")
            except Exception as e:
                logger.error(f"Error reading men dataset: {e}")
                scraper.errors.append(f"Men dataset error: {str(e)}")
        
        # Store products in MongoDB
        stored_count = 0
        for product in all_products:
            try:
                # Check if product already exists (by URL)
                existing = products_collection.find_one({"product_url": product["product_url"]})
                if not existing:
                    products_collection.insert_one(product)
                    stored_count += 1
                else:
                    # Update existing product
                    products_collection.update_one(
                        {"product_url": product["product_url"]},
                        {"$set": product}
                    )
            except Exception as e:
                logger.error(f"Error storing product: {e}")
                scraper.errors.append(f"Storage error: {str(e)}")
        
        await scraper.close()
        
        return {
            "total_scraped": scraper.scraped_count,
            "total_stored": stored_count,
            "failed": scraper.failed_count,
            "errors": scraper.errors[:10],  # Limit errors
            "products": len(all_products)
        }
    
    except Exception as e:
        logger.error(f"Error in scrape_from_excel_files: {e}")
        await scraper.close()
        return {
            "total_scraped": 0,
            "total_stored": 0,
            "failed": scraper.failed_count,
            "errors": [str(e)],
            "products": 0
        }



