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
import hashlib

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
                                   main_category: str, gender: Optional[str] = None, 
                                   price_range: str = None) -> List[Dict]:
        """
        Scrape products from a brand website.
        
        Args:
            brand_url: Base URL of the brand website
            brand_name: Name of the brand
            main_category: Main category from dataset
            gender: Gender of products ('m' for men, 'w' for women)
            price_range: Price range if available
        
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            # Use provided gender, or extract from main category if not provided
            if not gender:
                gender = extract_gender_from_category(main_category)
            
            # Ensure main_category is set correctly for men's brands
            if not main_category or main_category == "":
                # If no category provided and gender is men, set default
                if gender == "m":
                    main_category = "Men → Eastern"
                elif gender == "w":
                    main_category = "Women → Stitched"
            
            logger.info(f"Scraping brand: {brand_name} from {brand_url} (Category: {main_category}, Gender: {gender})")
            
            # FOR MEN'S BRANDS: Go directly to homepage and extract products
            if gender == "m":
                logger.info(f"Men's brand detected - using direct extraction method for {brand_name}")
                try:
                    # Step 1: Get homepage
                    response = await self.client.get(brand_url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        logger.info(f"Homepage loaded for {brand_name}")
                        
                        # Step 2: Try to extract products directly from homepage
                        direct_products = await self._extract_products_from_page(soup, brand_url, brand_name, main_category, gender)
                        if direct_products:
                            products.extend(direct_products)
                            logger.info(f"Extracted {len(direct_products)} products directly from homepage")
                        
                        # Step 3: Also try to find MEN link and extract from there
                        men_links = soup.find_all('a', href=True, string=re.compile(r'[Mm]en', re.I))
                        men_links.extend(soup.find_all('a', href=True, attrs={'href': re.compile(r'/men', re.I)}))
                        
                        for link in men_links[:3]:  # Try first 3 MEN links
                            href = link.get('href', '')
                            if href:
                                men_url = urljoin(brand_url, href)
                                logger.info(f"Trying MEN page: {men_url}")
                                try:
                                    men_response = await self.client.get(men_url)
                                    if men_response.status_code == 200:
                                        men_soup = BeautifulSoup(men_response.text, 'html.parser')
                                        men_products = await self._extract_products_from_page(men_soup, men_url, brand_name, main_category, gender)
                                        if men_products:
                                            products.extend(men_products)
                                            logger.info(f"Extracted {len(men_products)} products from MEN page")
                                except Exception as e:
                                    logger.debug(f"Error accessing MEN page {men_url}: {e}")
                        
                        # Step 4: If still no products, try common paths
                        if not products:
                            common_paths = ["/men", "/products", "/shop", "/products/men", "/shop/men"]
                            for path in common_paths:
                                try:
                                    path_url = urljoin(brand_url, path)
                                    logger.info(f"Trying path: {path_url}")
                                    path_response = await self.client.get(path_url)
                                    if path_response.status_code == 200:
                                        path_soup = BeautifulSoup(path_response.text, 'html.parser')
                                        path_products = await self._extract_products_from_page(path_soup, path_url, brand_name, main_category, gender)
                                        if path_products:
                                            products.extend(path_products)
                                            logger.info(f"Extracted {len(path_products)} products from {path_url}")
                                            break  # Found products, stop searching
                                except Exception as e:
                                    logger.debug(f"Error accessing {path_url}: {e}")
                                    continue
                    
                except Exception as e:
                    logger.error(f"Error in direct extraction for men's brand: {e}")
                    self.errors.append(f"{brand_url}: {str(e)}")
            else:
                # For women's brands, use normal method
                product_urls = await self._find_product_pages(brand_url)
                logger.info(f"Found {len(product_urls)} product URLs for {brand_name}")
                
                for product_url in product_urls[:50]:
                    try:
                        product = await self._scrape_product_page(
                            product_url, brand_name, main_category, gender, price_range
                        )
                        if product:
                            if not product.get('price') or product.get('price', 0) <= 0:
                                continue
                            products.append(product)
                            self.scraped_count += 1
                    except Exception as e:
                        logger.error(f"Error scraping product {product_url}: {e}")
                        self.failed_count += 1
            
            # Remove duplicates based on product name
            seen_names = set()
            unique_products = []
            for product in products:
                name = product.get('name', '').strip().lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_products.append(product)
            
            logger.info(f"Total unique products scraped for {brand_name}: {len(unique_products)}")
            return unique_products
        
        except Exception as e:
            logger.error(f"Error scraping brand {brand_url}: {e}")
            self.errors.append(f"{brand_url}: {str(e)}")
            return products
    
    async def _find_product_pages(self, base_url: str, prefer_men: bool = False) -> List[str]:
        """
        Find product listing pages on the website.
        This is a generic approach - may need customization per site.
        
        Args:
            base_url: Base URL of the website
            prefer_men: If True, prioritize men's stitched/unstitched pages
        """
        product_urls = []
        
        logger.info(f"Finding product pages for {base_url} (prefer_men={prefer_men})")
        
        try:
            # For men's brands, try homepage first to find MEN link and products
            if prefer_men:
                try:
                    logger.info(f"Trying homepage first for men's brand: {base_url}")
                    response = await self.client.get(base_url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # First, try to find products directly on homepage (some sites show products on homepage)
                        homepage_products = self._find_products_on_page(soup, base_url, prefer_men=True)
                        if homepage_products:
                            product_urls.extend(homepage_products)
                            logger.info(f"Found {len(homepage_products)} products on homepage")
                        
                        # Look for MEN link in navigation
                        men_links = soup.find_all('a', href=True, string=re.compile(r'[Mm]en', re.I))
                        men_links.extend(soup.find_all('a', href=True, attrs={'href': re.compile(r'/men', re.I)}))
                        
                        # Also look for any link containing "men" in href
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href', '')
                            if href and ('men' in href.lower() or 'man' in href.lower()):
                                if link not in men_links:
                                    men_links.append(link)
                        
                        for link in men_links:
                            href = link.get('href', '')
                            if href:
                                full_url = urljoin(base_url, href)
                                logger.info(f"Found MEN link: {full_url}")
                                # Try to get products from this page
                                try:
                                    men_response = await self.client.get(full_url)
                                    if men_response.status_code == 200:
                                        men_soup = BeautifulSoup(men_response.text, 'html.parser')
                                        # Find products on men's page
                                        men_page_products = self._find_products_on_page(men_soup, full_url, prefer_men=True)
                                        if men_page_products:
                                            product_urls.extend(men_page_products)
                                            logger.info(f"Found {len(men_page_products)} products from MEN page: {full_url}")
                                except Exception as e:
                                    logger.debug(f"Error accessing MEN page {full_url}: {e}")
                except Exception as e:
                    logger.debug(f"Error checking homepage for MEN link: {e}")
            
            # Common product listing page patterns
            if prefer_men:
                # For men's brands, prioritize stitched and unstitched
                common_paths = [
                    "/men",
                    "/men/stitched",
                    "/men/unstitched",
                    "/men/pret/stitched",
                    "/men/pret/unstitched",
                    "/men/eastern/stitched",
                    "/men/eastern/unstitched",
                    "/products/men/stitched",
                    "/products/men/unstitched",
                    "/shop/men/stitched",
                    "/shop/men/unstitched",
                    "/men/pret",
                    "/men/eastern",
                    "/men/products",
                    "/men/shop",
                    "/products/men",
                    "/shop/men",
                    "/products",
                    "/shop",
                ]
            else:
                # Default paths
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
                        
                        # Use the improved product finding method
                        found_products = self._find_products_on_page(soup, url, prefer_men=prefer_men)
                        if found_products:
                            for product_url in found_products:
                                if product_url not in product_urls:
                                    product_urls.append(product_url)
                        
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
        # For men's brands, return more products
        limit = 50 if prefer_men else 20
        return product_urls[:limit]
    
    def _find_products_on_page(self, soup: BeautifulSoup, base_url: str, prefer_men: bool = False) -> List[str]:
        """Find product URLs on a given page - more aggressive approach"""
        product_urls = []
        
        logger.debug(f"Finding products on page: {base_url} (prefer_men={prefer_men})")
        
        # Method 1: Look for product containers with links
        product_containers = soup.select('.product, .product-item, .product-card, [data-product-id], .item, .product-wrapper, .product-tile, .grid-item, [class*="product"], [class*="item"], article, [class*="card"], [class*="Product"]')
        
        logger.debug(f"Found {len(product_containers)} product containers")
        
        for container in product_containers:
            link = container.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href and not href.startswith('#') and not href.startswith('javascript:'):
                    full_url = urljoin(base_url, href)
                    if self._is_product_url(full_url, strict=not prefer_men):
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            logger.debug(f"Found product URL from container: {full_url}")
        
        # Method 2: Look for links with product-like patterns
        product_link_patterns = [
            'a[href*="/product"]',
            'a[href*="/item"]',
            'a[href*="/p/"]',
            'a[href*="/dp/"]',
            'a[href*="/shop/"]',
            'a[href*="/catalog/"]',
        ]
        
        for pattern in product_link_patterns:
            links = soup.select(pattern)
            for link in links:
                href = link.get('href', '')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_product_url(full_url, strict=not prefer_men):
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            logger.debug(f"Found product URL from pattern {pattern}: {full_url}")
        
        # Method 3: For men's brands, be even more lenient - look for any link that might be a product
        if prefer_men:
            all_links = soup.find_all('a', href=True)
            logger.debug(f"Checking {len(all_links)} total links for men's products")
            
            for link in all_links:
                href = link.get('href', '')
                if href and not href.startswith('#') and not href.startswith('javascript:'):
                    # Skip obvious non-product links
                    skip_patterns = ['/cart', '/checkout', '/account', '/login', '/register', '/signup', '/search', '/filter', '/category', '/collection', '/tag', '/blog', '/news', '/about', '/contact', '/help', '/faq', '/terms', '/privacy', '/policy']
                    
                    # For men's brands, also skip if it's clearly a listing/category page (but be lenient)
                    href_lower = href.lower()
                    is_listing_page = any(pattern in href_lower for pattern in ['/shop', '/products', '/catalog', '/collection', '/category'])
                    
                    # Only skip if it's a listing page AND we already have products, or if it's clearly not a product
                    if not any(pattern in href_lower for pattern in skip_patterns):
                        # For listing pages, only skip if we already found products from containers
                        if is_listing_page and product_urls:
                            continue
                            
                        full_url = urljoin(base_url, href)
                        # Very lenient check - just ensure it's not a file extension
                        url_parts = [p for p in full_url.lower().split('/') if p and p not in ['http:', 'https:', 'www.', '']]
                        if len(url_parts) >= 2:
                            # Check if it's not a file
                            if not any(full_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.pdf', '.xml', '.json']):
                                # Check if it's not the same as base URL
                                if full_url != base_url and full_url != base_url + '/':
                                    if full_url not in product_urls:
                                        product_urls.append(full_url)
                                        logger.debug(f"Found potential product URL (lenient mode): {full_url}")
        
        logger.info(f"Total product URLs found on page: {len(product_urls)}")
        return product_urls
    
    def _is_product_url(self, url: str, strict: bool = True) -> bool:
        """Check if URL looks like a product page - can be strict or lenient"""
        url_lower = url.lower()
        product_indicators = ['/product/', '/item/', '/p/', '/dp/', '/-p-', '/products/']
        exclude_patterns = [
            '/category/', '/collection/', '/shop/', '/cart/', '/checkout/', '/search', 
            '/filter', '/page=', '/tag=', '/logo', '/banner', '/header', '/footer',
            '/icon', '/image/', '/photo/', '/gallery/', '/about', '/contact', '/blog',
            '/news', '/help', '/faq', '/terms', '/privacy', '/policy', '/account',
            '/login', '/register', '/signup', '/wishlist', '/compare', '/review'
        ]
        
        # Exclude common non-product file extensions
        exclude_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.css', '.js', '.pdf']
        if any(url_lower.endswith(ext) for ext in exclude_extensions):
            return False
        
        # Check if it doesn't have exclude patterns
        has_exclude = any(pattern in url_lower for pattern in exclude_patterns)
        if has_exclude:
            return False
        
        # Check if it has product indicators
        has_product_indicator = any(ind in url_lower for ind in product_indicators)
        
        # Also check if URL has a product-like structure
        url_parts = [p for p in url_lower.split('/') if p and p not in ['http:', 'https:', 'www.', '']]
        has_product_structure = len(url_parts) >= 2 if not strict else len(url_parts) >= 3
        
        # URL should have meaningful product-like segments (not just navigation)
        meaningful_segments = ['product', 'item', 'p-', 'dp', 'detail', 'view']
        has_meaningful_segment = any(seg in url_lower for seg in meaningful_segments)
        
        # For strict mode: require product indicator OR (structure AND meaningful segment)
        # For lenient mode: accept if it has structure and doesn't match exclude patterns
        if strict:
            return (has_product_indicator or (has_product_structure and has_meaningful_segment))
        else:
            # Lenient mode: accept URLs that look like products (have structure, not excluded)
            # This helps find products on men's pages that might not have standard product indicators
            return has_product_structure and len(url_parts) >= 2
    
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
            
            # Generate unique product_id from URL hash (to avoid null product_id errors)
            # Use first 8 characters of MD5 hash converted to integer
            url_hash = hashlib.md5(product_url.encode('utf-8')).hexdigest()
            product_id = int(url_hash[:8], 16)  # Convert first 8 hex chars to int
            
            # Ensure category is set correctly - use main_category if available
            final_category = main_category if main_category else (product_category if product_category else "Other")
            
            # For men's products, detect if it's stitched or unstitched from URL or page content
            if gender == "m":
                product_url_lower = product_url.lower()
                page_text_lower = soup.get_text().lower() if soup else ""
                
                # Check URL and page content for stitched/unstitched indicators
                has_stitched = ("stitched" in product_url_lower or "pret" in product_url_lower or 
                               "stitched" in page_text_lower or "pret" in page_text_lower)
                has_unstitched = ("unstitched" in product_url_lower or "unstitched" in page_text_lower)
                
                # Determine category based on detection
                if has_stitched:
                    final_category = "Men → Stitched"
                elif has_unstitched:
                    final_category = "Men → Unstitched"
                elif "Men →" not in final_category:
                    # Default to Stitched if no clear indicator (similar to women's default)
                    final_category = "Men → Stitched"
                else:
                    # If category already has "Men →" but not Stitched/Unstitched, try to detect
                    if "eastern" in final_category.lower():
                        # Default Eastern to Stitched (most common)
                        final_category = final_category.replace("Eastern", "Stitched")
                    elif "→" in final_category and "stitched" not in final_category.lower() and "unstitched" not in final_category.lower():
                        # If category format is "Men → Something", keep it but ensure it's valid
                        pass
            
            # Ensure gender is set correctly - FOR MEN'S BRANDS, ALWAYS SET TO "m"
            if gender == "m":
                final_gender = "m"  # Always men for men's brands
            else:
                final_gender = gender if gender else ("m" if "men" in final_category.lower() or "man" in final_category.lower() else "w" if "women" in final_category.lower() or "woman" in final_category.lower() else None)
            
            # CRITICAL: For men's brands, validate product is actually for men
            if gender == "m":
                product_name_lower = product.get('name', '').lower()
                page_text_lower = soup.get_text().lower()
                
                # Check if product indicates it's for women
                women_indicators = [
                    'women', 'woman', 'girl', 'girls', 'ladies', 'lady', 'female',
                    'feminine', 'she', 'her', 'womens', 'womans', 'girls\'', 'ladies\'',
                    'kurti', 'kurtis', 'lehenga', 'saree', 'sari', 'dupatta', 'chunri',
                    'anarkali', 'gown', 'frock', 'skirt', 'top', 'blouse'
                ]
                
                # If product name or page text contains women's indicators, skip it
                if any(indicator in product_name_lower for indicator in women_indicators):
                    logger.debug(f"Skipping women's product from men's brand: {product.get('name')}")
                    return None
                
                if any(indicator in page_text_lower for indicator in women_indicators):
                    # Check if it's just mentioning women's section (not the actual product)
                    # If product name doesn't have women indicators, it might be OK
                    if any(indicator in product_name_lower for indicator in women_indicators):
                        logger.debug(f"Skipping women's product from men's brand (page text indicates women): {product.get('name')}")
                        return None
            
            # Extract product information (generic approach)
            product = {
                'product_id': product_id,  # Unique ID generated from URL
                'name': self._extract_product_name(soup),
                'brand': brand_name,
                'category': final_category,  # Use final category (ensures men's products have correct category)
                'product_category': product_category,  # Category from website
                'normalized_category': normalize_category(category_to_normalize, final_gender),
                'price': self._extract_price(soup, price_range),
                'image_url': self._extract_image_url(soup, product_url),
                'product_url': product_url,
                'description': self._extract_description(soup),
                'scraped_at': datetime.utcnow(),
                'gender': final_gender,  # Ensure gender is set correctly
                'broken_link': False,
            }
            
            # Validate product - filter out logos, placeholders, and non-products
            product_name = product.get('name', '').strip()
            image_url = product.get('image_url', '').strip()
            
            # Skip if name is invalid (too short, is placeholder, or is logo text)
            invalid_names = [
                'echtr', 'logo', 'placeholder', 'image', 'photo', 'picture', 'unknown', 'loading', 'error', '404', 'not found',
                'banner', 'header', 'footer', 'menu', 'nav', 'search', 'cart', 'account', 'login', 'register', 'signup',
                'home', 'shop', 'products', 'category', 'collection', 'about', 'contact', 'help', 'faq', 'terms', 'privacy',
                'policy', 'news', 'blog', 'instagram', 'facebook', 'twitter', 'youtube', 'social', 'share', 'follow',
                'subscribe', 'newsletter', 'email', 'phone', 'address', 'location', 'map', 'delivery', 'shipping', 'return',
                'refund', 'wishlist', 'compare', 'filter', 'sort', 'view', 'grid', 'list', 'page', 'next', 'previous',
                'prev', 'back', 'close', 'open', 'more', 'less', 'all', 'new', 'sale', 'discount', 'offer', 'deal',
                'promo', 'coupon', 'icon', 'arrow', 'chevron', 'hamburger', 'mobile', 'desktop', 'dropdown'
            ]
            if not product_name or len(product_name) < 5:  # Minimum 5 characters
                logger.debug(f"Skipping product: name too short or empty - {product_url}")
                return None
            if any(invalid in product_name.lower() for invalid in invalid_names):
                logger.debug(f"Skipping product: invalid name - {product_name}")
                return None
            
            # Check for generic/placeholder names
            name_words = product_name.split()
            generic_words = ['product', 'item', 'new', 'sale', 'discount', 'offer', 'deal', 'view', 'see', 'more', 'all', 'shop', 'buy']
            if len(name_words) == 1 and product_name.lower() in generic_words:
                logger.debug(f"Skipping product: generic name - {product_name}")
                return None
            
            # Check if name is just numbers or symbols
            if product_name.replace(' ', '').replace('-', '').isdigit():
                logger.debug(f"Skipping product: numeric-only name - {product_name}")
                return None
            
            # For men's brands, be more lenient with image URL
            if gender == "m":
                # Allow products even if image URL is missing or looks like a placeholder
                if not image_url:
                    logger.warning(f"Product {product_name} has no image URL, but keeping it for men's brand")
                    product['image_url'] = 'https://via.placeholder.com/300?text=No+Image'
                else:
                    invalid_image_patterns = ['logo', 'placeholder', 'default', 'no-image', 'not-found', '404', 'icon', 'banner', 'header', 'footer']
                    if any(pattern in image_url.lower() for pattern in invalid_image_patterns):
                        logger.warning(f"Product {product_name} has placeholder image, but keeping it for men's brand")
                        # Don't skip, just log warning
            else:
                # For women's brands, require valid image
                if not image_url:
                    logger.debug(f"Skipping product: no image URL - {product_url}")
                    return None
                
                # Comprehensive image URL validation for women's products
                invalid_image_patterns = [
                    'logo', 'placeholder', 'default', 'no-image', 'not-found', '404', 'icon', 'banner', 'header', 'footer',
                    'nav', 'menu', 'social', 'facebook', 'instagram', 'twitter', 'youtube', 'pinterest', 'whatsapp',
                    'linkedin', 'share', 'cart', 'search', 'user', 'account', 'login', 'arrow', 'chevron', 'close',
                    'menu-icon', 'hamburger', 'mobile-menu', 'desktop-menu', 'dropdown', 'favicon', 'apple-touch',
                    '16x16', '32x32', '48x48', '64x64'
                ]
                image_url_lower = image_url.lower()
                if any(pattern in image_url_lower for pattern in invalid_image_patterns):
                    logger.debug(f"Skipping product: invalid image URL (logo/icon) - {image_url}")
                    return None
                
                # Check for single-letter logos or text-based logos in filename
                # Common patterns: single letter (G.jpg, A.png), text logos (logo-G.png, brand-G.jpg)
                import re
                filename = image_url.split('/')[-1].lower()
                # Check if filename is just a single letter or contains single-letter patterns
                if re.match(r'^[a-z]\.(jpg|jpeg|png|gif|webp)$', filename) or re.search(r'[^a-z][a-z]\.(jpg|jpeg|png|gif|webp)$', filename):
                    logger.debug(f"Skipping product: single-letter logo image - {image_url}")
                    return None
                
                # Check for text-based logo patterns (echtr, logo-text, etc.)
                if any(text in filename for text in ['echtr', 'logo-', '-logo', 'brand-', '-brand', 'icon-', '-icon']):
                    logger.debug(f"Skipping product: text-based logo image - {image_url}")
                    return None
                
                # Check if image URL contains single-letter patterns (like /G/, /A/, etc.)
                if re.search(r'/[a-z]/[a-z]\.(jpg|jpeg|png|gif|webp)', image_url_lower):
                    logger.debug(f"Skipping product: single-letter logo in path - {image_url}")
                    return None
            
            # For men's brands, be lenient with price - set default if missing
            if gender == "m":
                if not product.get('price') or product.get('price', 0) <= 0:
                    logger.warning(f"Product {product_name} has no price, setting default for men's brand")
                    product['price'] = 1000.0  # Default price
            else:
                # For women's brands, require valid price
                price = product.get('price', 0)
                if not price or price <= 0:
                    logger.debug(f"Skipping product: no price - {product_url}")
                    return None
                
                # Filter out unrealistic prices (too low - likely placeholder/error)
                # Minimum reasonable price for women's clothing in PKR (e.g., 500 PKR)
                if price < 500:
                    logger.debug(f"Skipping product: unrealistic price (too low) - {product_name}: PKR {price}")
                    return None
                
                # Filter out unrealistic prices (too high - likely error)
                if price > 100000:
                    logger.debug(f"Skipping product: unrealistic price (too high) - {product_name}: PKR {price}")
                    return None
            
            # Additional validation: product name should have meaningful content
            # For men's brands, be more lenient with single-word names
            if gender != "m":
                # Filter out single words that are likely categories or placeholders (only for women's)
                name_words = product_name.split()
                valid_single_words = ['kurta', 'shirt', 'kameez', 'shalwar', 'suit', 'dress', 'trouser', 'pant', 'jacket', 'coat']
                if len(name_words) < 2 and product_name.lower() not in valid_single_words:
                    logger.debug(f"Skipping product: single word name (not valid category) - {product_name}")
                    return None
                
                # Additional check: if name is too generic or looks like a collection/category name
                product_name_lower = product_name.lower()
                if any(word in product_name_lower for word in ['collection:', 'collection', 'set:', 'set', 'category:', 'category']):
                    # If it's just "Collection: X" or "Set: Y", it might be a placeholder
                    if len(name_words) <= 3:
                        logger.debug(f"Skipping product: generic collection/category name - {product_name}")
                        return None
            
            # Validate it's a real product page (has meaningful name)
            if product_name:
                logger.info(f"Valid product found: {product_name} - Price: {product.get('price')} - Image: {product.get('image_url')}")
                return product
            
            return None
        
        except Exception as e:
            logger.error(f"Error scraping product page {product_url}: {e}")
            return None
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name from page - with validation"""
        # Try common selectors
        selectors = [
            'h1.product-title',
            'h1.product-name',
            'h1[itemprop="name"]',
            '.product-title',
            '.product-name',
            'h1',
            '[data-product-name]',
            '.product-details h1',
            '.product-info h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                # Validate name - should not be placeholder or logo text
                invalid_names = ['echtr', 'logo', 'placeholder', 'image', 'photo', 'loading', 'error']
                if name and len(name) > 2 and not any(invalid in name.lower() for invalid in invalid_names):
                    return name
        
        return ""
    
    def _extract_price(self, soup: BeautifulSoup, price_range: str = None) -> Optional[float]:
        """Extract product price from page - handles PKR, Rs., etc."""
        # Try common price selectors
        selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.amount',
            '.cost',
            '[class*="price"]',
            '[class*="Price"]',
            '.price-current',
            '.sale-price',
            '.regular-price',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numbers (handle PKR, Rs., commas, etc.)
                # Remove currency symbols and extract numbers
                price_text_clean = re.sub(r'[^\d.,]', '', price_text.replace(',', ''))
                numbers = re.findall(r'[\d.]+', price_text_clean)
                if numbers:
                    try:
                        price = float(numbers[0])
                        if price > 0:
                            return price
                    except:
                        pass
        
        # Also try to find price in text content (for sites that don't use standard selectors)
        page_text = soup.get_text()
        # Look for patterns like "Rs.7,180.00" or "PKR 7180" or "Rs 7,180"
        price_patterns = [
            r'[Rr][Ss]\.?\s*([\d,]+\.?\d*)',
            r'[Pp][Kk][Rr]\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*[Rr][Ss]',
            r'([\d,]+\.?\d*)\s*[Pp][Kk][Rr]',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                try:
                    price_str = matches[0].replace(',', '')
                    price = float(price_str)
                    if price > 0:
                        return price
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
        """Extract product image URL - improved to handle lazy loading and prioritize high-resolution images"""
        # Priority: High-res images first (zoom, original, large)
        high_res_attributes = [
            'data-zoom-image',  # Zoom images are usually high-res
            'data-original',    # Original images
            'data-large',       # Large images
            'data-hd',          # HD images
            'data-full',        # Full size images
            'data-image',       # Main product image
        ]
        
        # Try common image selectors with priority
        selectors = [
            'img.product-image',
            'img[itemprop="image"]',
            '.product-image img',
            '.product-gallery img',
            '.product-gallery-main img',
            '.product-main-image img',
            '.product-photo img',
            '.product-thumbnail img',
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
        ]
        
        best_image_url = None
        best_priority = 0  # Higher = better (high-res)
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # First, try high-res attributes
                for attr in high_res_attributes:
                    img_url = element.get(attr)
                    if img_url:
                        img_url_lower = img_url.lower()
                        # Skip placeholder/logo images
                        if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default', 'no-image', 'not-found', '404']):
                            continue
                        full_url = urljoin(base_url, img_url)
                        # Validate it's a real image URL
                        if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']) or 'image' in full_url.lower():
                            # High priority for zoom/original images
                            priority = 10 if 'zoom' in attr or 'original' in attr else 8
                            if priority > best_priority:
                                best_image_url = full_url
                                best_priority = priority
                
                # Then try regular attributes
                img_url = (
                    element.get('src') or 
                    element.get('data-src') or 
                    element.get('data-lazy-src') or 
                    element.get('content')
                )
                
                if img_url:
                    # Handle srcset - prefer larger images
                    if element.get('srcset'):
                        srcset = element.get('srcset')
                        # Parse srcset to get largest image
                        # Format: "url1 1x, url2 2x, url3 800w"
                        srcset_parts = [p.strip() for p in srcset.split(',')]
                        largest_url = None
                        largest_size = 0
                        for part in srcset_parts:
                            parts = part.strip().split()
                            if len(parts) >= 1:
                                url = parts[0]
                                # Check for size descriptor (2x, 800w, etc.)
                                size = 0
                                if len(parts) > 1:
                                    size_desc = parts[1].lower()
                                    if 'x' in size_desc:
                                        size = float(size_desc.replace('x', '')) * 100
                                    elif 'w' in size_desc:
                                        size = float(size_desc.replace('w', ''))
                                if size > largest_size:
                                    largest_size = size
                                    largest_url = url
                        if largest_url:
                            img_url = largest_url
                    
                    # Handle srcset in data attribute
                    if element.get('data-srcset'):
                        srcset = element.get('data-srcset')
                        srcset_parts = [p.strip() for p in srcset.split(',')]
                        largest_url = None
                        largest_size = 0
                        for part in srcset_parts:
                            parts = part.strip().split()
                            if len(parts) >= 1:
                                url = parts[0]
                                size = 0
                                if len(parts) > 1:
                                    size_desc = parts[1].lower()
                                    if 'x' in size_desc:
                                        size = float(size_desc.replace('x', '')) * 100
                                    elif 'w' in size_desc:
                                        size = float(size_desc.replace('w', ''))
                                if size > largest_size:
                                    largest_size = size
                                    largest_url = url
                        if largest_url:
                            img_url = largest_url
                    
                    # Skip placeholder/logo images
                    img_url_lower = img_url.lower()
                    if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default', 'no-image', 'not-found', '404']):
                        continue
                    
                    full_url = urljoin(base_url, img_url)
                    # Remove size restrictions from URL to get original (e.g., ?w=300 -> remove it)
                    full_url = self._remove_size_restrictions(full_url)
                    
                    # Validate it's a real image URL
                    if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']) or 'image' in full_url.lower():
                        # Check if it's a high-res image
                        priority = 5
                        if any(keyword in full_url.lower() for keyword in ['large', 'original', 'hd', 'high', 'full', 'zoom', 'big']):
                            priority = 7
                        if any(keyword in full_url.lower() for keyword in ['thumb', 'small', 'mini']):
                            priority = 3  # Lower priority for thumbnails
                        
                        if priority > best_priority:
                            best_image_url = full_url
                            best_priority = priority
        
        if best_image_url:
            return best_image_url
        
        # Fallback: find first large image in product containers (prioritize high-res)
        product_containers = soup.select('.product, .product-item, .product-card, .product-wrapper, .product-tile, [data-product-id]')
        for container in product_containers:
            img = container.find('img')
            if img:
                # Try high-res attributes first
                for attr in high_res_attributes:
                    img_url = img.get(attr)
                    if img_url:
                        img_url_lower = img_url.lower()
                        if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default']):
                            continue
                        full_url = urljoin(base_url, img_url)
                        full_url = self._remove_size_restrictions(full_url)
                        if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']) or 'image' in full_url.lower():
                            priority = 10 if 'zoom' in attr or 'original' in attr else 8
                            if priority > best_priority:
                                best_image_url = full_url
                                best_priority = priority
                
                # Then try regular attributes
                img_url = (
                    img.get('src') or 
                    img.get('data-src') or 
                    img.get('data-lazy-src')
                )
                if img_url:
                    img_url_lower = img_url.lower()
                    # Skip logos/placeholders
                    if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default']):
                        continue
                    full_url = urljoin(base_url, img_url)
                    full_url = self._remove_size_restrictions(full_url)
                    # Prefer larger images
                    priority = 5
                    if any(keyword in full_url.lower() for keyword in ['large', 'original', 'hd', 'high', 'full']):
                        priority = 7
                    if any(keyword in full_url.lower() for keyword in ['thumb', 'small', 'mini']):
                        priority = 3
                    if priority > best_priority:
                        best_image_url = full_url
                        best_priority = priority
        
        if best_image_url:
            return best_image_url
        
        # Last fallback: find any image that looks like a product image (prioritize high-res)
        images = soup.find_all('img')
        for img in images:
            # Try high-res attributes first
            for attr in high_res_attributes:
                img_url = img.get(attr)
                if img_url:
                    img_url_lower = img_url.lower()
                    if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default', 'favicon', 'social', 'header', 'footer']):
                        continue
                    full_url = urljoin(base_url, img_url)
                    full_url = self._remove_size_restrictions(full_url)
                    if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                        priority = 10 if 'zoom' in attr or 'original' in attr else 8
                        if priority > best_priority:
                            best_image_url = full_url
                            best_priority = priority
            
            # Then try regular attributes
            img_url = (
                img.get('src') or 
                img.get('data-src') or 
                img.get('data-lazy-src')
            )
            if img_url:
                img_url_lower = img_url.lower()
                # Skip obvious non-product images
                if any(pattern in img_url_lower for pattern in ['logo', 'icon', 'banner', 'placeholder', 'default', 'favicon', 'social', 'header', 'footer']):
                    continue
                # Prefer images with product-related keywords
                full_url = urljoin(base_url, img_url)
                full_url = self._remove_size_restrictions(full_url)
                priority = 5
                if any(keyword in full_url.lower() for keyword in ['product', 'item', 'catalog', 'collection', 'shop', 'store']):
                    priority = 6
                if any(keyword in full_url.lower() for keyword in ['large', 'original', 'hd', 'high', 'full']):
                    priority = 7
                if any(keyword in full_url.lower() for keyword in ['thumb', 'small', 'mini']):
                    priority = 3
                if any(ext in full_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                    if priority > best_priority:
                        best_image_url = full_url
                        best_priority = priority
        
        if best_image_url:
            return best_image_url
        
        return ""
    
    def _remove_size_restrictions(self, url: str) -> str:
        """Remove size restrictions from image URL to get original/high-res version"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Remove common size parameters
            size_params = ['w', 'width', 'h', 'height', 'size', 'resize', 'scale', 'fit', 'crop']
            for param in size_params:
                query_params.pop(param, None)
            
            # Rebuild URL without size parameters
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            new_url = urlunparse(new_parsed)
            
            # Also try to replace common size patterns in path
            # e.g., /300x300/ -> /original/ or /large/
            import re
            new_url = re.sub(r'/\d+x\d+/', '/original/', new_url)
            new_url = re.sub(r'/\d+/', '/original/', new_url)  # Single number like /300/
            new_url = re.sub(r'/(thumb|thumbnail|small|mini)/', '/large/', new_url, flags=re.IGNORECASE)
            
            return new_url
        except Exception:
            # If parsing fails, return original URL
            return url
    
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
    
    async def _extract_products_from_page(self, soup: BeautifulSoup, page_url: str, brand_name: str, 
                                          main_category: str, gender: Optional[str]) -> List[Dict]:
        """
        Extract products directly from a listing page (like homepage or category page)
        This is for cases where products are listed on the page itself, not as separate product pages
        """
        products = []
        
        try:
            # Look for product containers on the page - VERY AGGRESSIVE SELECTORS
            product_containers = soup.select('.product, .product-item, .product-card, [data-product-id], .item, .product-wrapper, .product-tile, .grid-item, [class*="product"], [class*="item"], article, [class*="card"], [class*="Product"], [class*="product"], div[class*="col"], li[class*="product"], li[class*="item"]')
            
            # If no containers found, try to find ANY divs/li that might contain products
            if not product_containers:
                # Look for any div or li that has an image and text
                all_divs = soup.find_all(['div', 'li', 'article'], class_=True)
                for div in all_divs:
                    # Check if it has an image and some text
                    img = div.find('img')
                    text = div.get_text(strip=True)
                    if img and text and len(text) > 10:
                        product_containers.append(div)
            
            logger.info(f"Found {len(product_containers)} potential product containers on page: {page_url}")
            
            for container in product_containers[:100]:  # Check up to 100 containers
                try:
                    # Extract product name - try multiple methods
                    product_name = ""
                    
                    # Method 1: Look for headings
                    name_elem = container.select_one('h1, h2, h3, h4, h5, h6, .title, .name, [class*="title"], [class*="name"], [class*="Title"], [class*="Name"]')
                    if name_elem:
                        product_name = name_elem.get_text(strip=True)
                    
                    # Method 2: Look for links with text
                    if not product_name:
                        link = container.find('a')
                        if link:
                            link_text = link.get_text(strip=True)
                            if link_text and len(link_text) > 3:
                                product_name = link_text
                    
                    # Method 3: Get first meaningful text from container
                    if not product_name:
                        container_text = container.get_text(strip=True)
                        # Split by newlines and get first meaningful line
                        lines = [line.strip() for line in container_text.split('\n') if line.strip()]
                        for line in lines:
                            if len(line) > 5 and len(line) < 200:  # Reasonable product name length
                                product_name = line
                                break
                    
                    # Skip if name is invalid
                    if not product_name or len(product_name) < 3:
                        continue
                    
                    # Comprehensive filtering for logos, placeholders, and non-product items
                    invalid_names = [
                        'echtr', 'logo', 'placeholder', 'image', 'photo', 'loading', 'error', '404',
                        'banner', 'header', 'footer', 'menu', 'nav', 'search', 'cart', 'account',
                        'login', 'register', 'signup', 'home', 'shop', 'products', 'category',
                        'collection', 'about', 'contact', 'help', 'faq', 'terms', 'privacy',
                        'policy', 'news', 'blog', 'instagram', 'facebook', 'twitter', 'youtube',
                        'social', 'share', 'follow', 'subscribe', 'newsletter', 'email', 'phone',
                        'address', 'location', 'map', 'delivery', 'shipping', 'return', 'refund',
                        'wishlist', 'compare', 'filter', 'sort', 'view', 'grid', 'list', 'page',
                        'next', 'previous', 'prev', 'back', 'close', 'open', 'more', 'less',
                        'all', 'new', 'sale', 'discount', 'offer', 'deal', 'promo', 'coupon',
                        'icon', 'arrow', 'chevron', 'hamburger', 'mobile', 'desktop', 'dropdown'
                    ]
                    
                    product_name_lower = product_name.lower()
                    if any(invalid in product_name_lower for invalid in invalid_names):
                        logger.debug(f"Skipping non-product item: {product_name}")
                        continue
                    
                    # Check if name looks like a product (should have meaningful words, not just single generic word)
                    name_words = product_name.split()
                    if len(name_words) < 2:
                        # Single word names are usually not products (except valid categories)
                        valid_single_words = ['kurta', 'shirt', 'kameez', 'shalwar', 'suit', 'dress', 'trouser', 'pant', 'jacket', 'coat', 'vest', 'waistcoat']
                        if product_name_lower not in valid_single_words:
                            logger.debug(f"Skipping single word (likely not product): {product_name}")
                            continue
                    
                    # Check if name is too generic (like just "Product", "Item", "New")
                    generic_words = ['product', 'item', 'new', 'sale', 'discount', 'offer', 'deal', 'view', 'see', 'more', 'all', 'shop', 'buy']
                    if len(name_words) == 1 and product_name_lower in generic_words:
                        logger.debug(f"Skipping generic word: {product_name}")
                        continue
                    
                    # CRITICAL: For men's brands, validate that product is actually for men (check early)
                    if gender == "m":
                        # Get container text for validation
                        container_text = container.get_text(strip=True)
                        container_text_lower = container_text.lower()
                        
                        # Check if product name or text indicates it's for women/girls
                        women_indicators = [
                            'women', 'woman', 'girl', 'girls', 'ladies', 'lady', 'female',
                            'feminine', 'she', 'her', 'womens', 'womans', 'girls\'', 'ladies\'',
                            'kurti', 'kurtis', 'lehenga', 'saree', 'sari', 'dupatta', 'chunri',
                            'anarkali', 'gown', 'frock', 'skirt', 'top', 'blouse'
                        ]
                        
                        # If product name contains women's indicators, skip it immediately
                        if any(indicator in product_name_lower for indicator in women_indicators):
                            logger.debug(f"Skipping women's product from men's brand (name): {product_name}")
                            continue
                        
                        # Check container text for women's indicators (but be careful - might just be navigation)
                        if container_text_lower:
                            # Count how many women indicators are in the text
                            women_count = sum(1 for indicator in women_indicators if indicator in container_text_lower)
                            # If multiple women indicators or product name also has them, skip
                            if women_count > 0 and any(indicator in product_name_lower for indicator in women_indicators):
                                logger.debug(f"Skipping women's product from men's brand (text + name): {product_name}")
                                continue
                    
                    # Extract price - try multiple methods
                    price = None
                    
                    # Method 1: Look for price elements
                    price_elem = container.select_one('.price, .product-price, [class*="price"], [class*="Price"], [class*="cost"], [class*="amount"]')
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price = self._extract_price_from_text(price_text)
                    
                    # Method 2: Look in container text
                    if not price:
                        container_text = container.get_text()
                        price = self._extract_price_from_text(container_text)
                    
                    # Extract image - prioritize high-resolution images
                    image_url = ""
                    img_elem = container.select_one('img')
                    if img_elem:
                        # Priority: High-res attributes first (zoom, original, large, hd, full)
                        high_res_attrs = ['data-zoom-image', 'data-original', 'data-large', 'data-hd', 'data-full', 'data-image']
                        for attr in high_res_attrs:
                            image_url = img_elem.get(attr)
                            if image_url:
                                break
                        
                        # Fallback to regular attributes
                        if not image_url:
                            image_url = (
                                img_elem.get('src') or 
                                img_elem.get('data-src') or 
                                img_elem.get('data-lazy-src')
                            )
                        
                        if image_url:
                            # Handle srcset - prefer largest image
                            if img_elem.get('srcset'):
                                srcset = img_elem.get('srcset')
                                srcset_parts = [p.strip() for p in srcset.split(',')]
                                largest_url = None
                                largest_size = 0
                                for part in srcset_parts:
                                    parts = part.strip().split()
                                    if len(parts) >= 1:
                                        url = parts[0]
                                        size = 0
                                        if len(parts) > 1:
                                            size_desc = parts[1].lower()
                                            if 'x' in size_desc:
                                                size = float(size_desc.replace('x', '')) * 100
                                            elif 'w' in size_desc:
                                                size = float(size_desc.replace('w', ''))
                                        if size > largest_size:
                                            largest_size = size
                                            largest_url = url
                                if largest_url:
                                    image_url = largest_url
                            
                            # Handle srcset in data attribute
                            if img_elem.get('data-srcset'):
                                srcset = img_elem.get('data-srcset')
                                srcset_parts = [p.strip() for p in srcset.split(',')]
                                largest_url = None
                                largest_size = 0
                                for part in srcset_parts:
                                    parts = part.strip().split()
                                    if len(parts) >= 1:
                                        url = parts[0]
                                        size = 0
                                        if len(parts) > 1:
                                            size_desc = parts[1].lower()
                                            if 'x' in size_desc:
                                                size = float(size_desc.replace('x', '')) * 100
                                            elif 'w' in size_desc:
                                                size = float(size_desc.replace('w', ''))
                                        if size > largest_size:
                                            largest_size = size
                                            largest_url = url
                                if largest_url:
                                    image_url = largest_url
                            
                            image_url = urljoin(page_url, image_url)
                            # Remove size restrictions to get original/high-res version
                            image_url = self._remove_size_restrictions(image_url)
                            
                            # Filter out logos, icons, banners, placeholders
                            invalid_image_patterns = [
                                'logo', 'icon', 'banner', 'placeholder', 'default', 'no-image',
                                'not-found', '404', 'header', 'footer', 'nav', 'menu', 'social',
                                'facebook', 'instagram', 'twitter', 'youtube', 'pinterest',
                                'whatsapp', 'linkedin', 'share', 'cart', 'search', 'user',
                                'account', 'login', 'arrow', 'chevron', 'close', 'menu-icon',
                                'hamburger', 'mobile-menu', 'desktop-menu', 'dropdown'
                            ]
                            
                            image_url_lower = image_url.lower()
                            if any(pattern in image_url_lower for pattern in invalid_image_patterns):
                                logger.debug(f"Skipping logo/icon image: {image_url}")
                                image_url = ""
                            
                            # Also check if image dimensions are too small (likely an icon)
                            # We can't check dimensions directly, but we can check filename patterns
                            if image_url and any(x in image_url_lower for x in ['16x16', '32x32', '48x48', '64x64', 'favicon', 'apple-touch']):
                                logger.debug(f"Skipping small icon image: {image_url}")
                                image_url = ""
                    
                    # Extract product URL if available
                    link_elem = container.find('a', href=True)
                    product_url = ""
                    if link_elem:
                        product_url = urljoin(page_url, link_elem.get('href', ''))
                    else:
                        product_url = page_url
                    
                    # CRITICAL: For men's brands, check URL for women's indicators BEFORE processing
                    if gender == "m" and product_url:
                        product_url_lower = product_url.lower()
                        women_url_indicators = ['women', 'woman', 'girl', 'ladies', 'kurti', 'lehenga', 'saree', '/w/', '/women/', '/woman/', '/girl/', '/ladies/']
                        if any(indicator in product_url_lower for indicator in women_url_indicators):
                            logger.debug(f"Skipping women's product from men's brand (URL): {product_url}")
                            continue
                    
                    # CRITICAL: For men's brands, check image URL for women's indicators
                    if gender == "m" and image_url:
                        image_url_lower = image_url.lower()
                        women_image_indicators = ['women', 'woman', 'girl', 'ladies', 'kurti', 'lehenga', 'saree', 'female', 'ladies']
                        if any(indicator in image_url_lower for indicator in women_image_indicators):
                            logger.debug(f"Skipping women's product from men's brand (image URL): {image_url[:50]}")
                            continue
                    
                    # Generate product ID
                    url_hash = hashlib.md5((product_url + product_name).encode('utf-8')).hexdigest()
                    product_id = int(url_hash[:8], 16)
                    
                    # Set category - FOR MEN'S BRANDS, ALWAYS SET MEN'S CATEGORY
                    if gender == "m":
                        # For men's brands, always use men's category
                        if main_category and "Men →" in main_category:
                            final_category = main_category
                        else:
                            final_category = "Men → Stitched"  # Default for men's products
                    else:
                        final_category = main_category if main_category else "Women → Stitched"
                    
                    # For men's brands, set default price if missing
                    if not price or price <= 0:
                        if gender == "m":
                            price = 1000.0  # Default price
                        else:
                            continue  # Skip if no price for women's
                    
                    # Additional validation: Check if container has meaningful product content
                    container_text = container.get_text(strip=True)
                    if len(container_text) < 15:  # Too short, likely not a product
                        logger.debug(f"Skipping container with too little text: {container_text[:50]}")
                        continue
                    
                    # Check if text contains navigation/menu words (likely not a product)
                    text_lower = container_text.lower()
                    nav_words = ['menu', 'navigation', 'search', 'cart', 'account', 'login', 'register', 'sign up', 'sign in', 'home', 'about', 'contact', 'help', 'faq']
                    if any(nav_word in text_lower for nav_word in nav_words) and len(name_words) < 3:
                        logger.debug(f"Skipping navigation/menu item: {product_name}")
                        continue
                    
                    # Check if image exists and is valid
                    if not image_url:
                        # For men's brands, allow products without images if they have good name and price
                        if gender == "m":
                            image_url = 'https://via.placeholder.com/300?text=No+Image'
                        else:
                            # For women's brands, require image
                            logger.debug(f"Skipping product without image: {product_name}")
                            continue
                    else:
                        # Additional image validation: Check if image URL looks like a product image
                        # Product images usually have certain patterns (not logos/icons)
                        img_url_lower = image_url.lower()
                        # Check if it's likely a product image (has product-related keywords or is in product directory)
                        product_image_indicators = ['product', 'item', 'catalog', 'collection', 'shop', 'store', 'image', 'photo', 'picture', 'jpg', 'jpeg', 'png', 'webp']
                        is_likely_product_image = any(indicator in img_url_lower for indicator in product_image_indicators)
                        
                        # If image doesn't look like a product image and name is generic, skip
                        if not is_likely_product_image and len(name_words) < 3:
                            logger.debug(f"Skipping item with non-product image: {product_name} - {image_url[:50]}")
                            continue
                    
                    # Final check: Ensure we have at least name and price (minimum requirements)
                    if not product_name or not price or price <= 0:
                        logger.debug(f"Skipping incomplete product: name={product_name}, price={price}")
                        continue
                    
                    # Additional check: Product name should not be just numbers or symbols
                    if product_name.replace(' ', '').replace('-', '').isdigit():
                        logger.debug(f"Skipping numeric-only name: {product_name}")
                        continue
                    
                    # Check if price is reasonable (not too high, likely a real product price)
                    if price > 100000:  # Unlikely to be a real product price
                        logger.debug(f"Skipping item with unrealistic price: {product_name} - {price}")
                        continue
                    
                    product = {
                        'product_id': product_id,
                        'name': product_name,
                        'brand': brand_name,
                        'category': final_category,
                        'product_category': "",
                        'normalized_category': normalize_category(final_category, gender),
                        'price': price,
                        'image_url': image_url,
                        'product_url': product_url,
                        'description': "",
                        'scraped_at': datetime.utcnow(),
                        'gender': "m" if gender == "m" else (gender or "w"),  # Always "m" for men's brands
                        'broken_link': False,
                    }
                    
                    products.append(product)
                    logger.info(f"✓ Extracted product: {product_name} - Price: {price} - Image: {image_url[:50] if image_url else 'None'}")
                    
                except Exception as e:
                    logger.debug(f"Error extracting product from container: {e}")
                    continue
            
            logger.info(f"Total products extracted from {page_url}: {len(products)}")
            
        except Exception as e:
            logger.error(f"Error extracting products from page {page_url}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return products
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text - handles PKR, Rs., etc."""
        if not text:
            return None
        
        # Remove currency symbols and extract numbers
        price_patterns = [
            r'[Rr][Ss]\.?\s*([\d,]+\.?\d*)',
            r'[Pp][Kk][Rr]\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*[Rr][Ss]',
            r'([\d,]+\.?\d*)\s*[Pp][Kk][Rr]',
            r'([\d,]+\.?\d*)',  # Just numbers
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    price_str = matches[0].replace(',', '')
                    price = float(price_str)
                    if price > 0:
                        return price
                except:
                    pass
        
        return None


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
        
        # Read men's brands from local_brands_links.csv (for local brand type only)
        if brand_type == "local":
            import os
            csv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "local_brands_links.csv")
            if os.path.exists(csv_file):
                try:
                    df_csv = pd.read_csv(csv_file)
                    logger.info(f"Read {len(df_csv)} rows from local_brands_links.csv")
                    
                    # CSV has Brand and Website columns
                    if "Brand" in df_csv.columns and "Website" in df_csv.columns:
                        for idx, row in df_csv.iterrows():
                            brand_name = row.get("Brand", "")
                            brand_url = row.get("Website", "")
                            
                            if pd.notna(brand_name) and pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                                # Default category for men's brands from CSV
                                main_category = "Men → Eastern"
                                
                                logger.info(f"Scraping {brand_name} from {brand_url} (Category: {main_category})")
                                products = await scraper.scrape_brand_website(
                                    brand_url, brand_name, main_category, None
                                )
                                all_products.extend(products)
                                
                                # Small delay to avoid overwhelming servers
                                await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error reading local_brands_links.csv: {e}")
                    scraper.errors.append(f"Men CSV error: {str(e)}")
        
        # Store products in MongoDB
        stored_count = 0
        for product in all_products:
            try:
                # Check if product already exists (by URL)
                existing = products_collection.find_one({"product_url": product.get("product_url")})
                if not existing:
                    # Ensure product_id exists (generate if missing)
                    if not product.get("product_id"):
                        import hashlib
                        url_hash = hashlib.md5(product.get("product_url", "").encode('utf-8')).hexdigest()
                        product["product_id"] = int(url_hash[:8], 16)
                    
                    # Check if product_id already exists (handle hash collisions)
                    product_id = product.get("product_id")
                    if product_id:
                        id_exists = products_collection.find_one({"product_id": product_id})
                        if id_exists:
                            # Generate new product_id by appending timestamp
                            url_hash = hashlib.md5(
                                f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                            ).hexdigest()
                            product["product_id"] = int(url_hash[:8], 16)
                    
                    products_collection.insert_one(product)
                    stored_count += 1
                else:
                    # Update existing product (preserve existing product_id)
                    update_data = product.copy()
                    if 'product_id' in update_data:
                        del update_data['product_id']
                    products_collection.update_one(
                        {"product_url": product.get("product_url")},
                        {"$set": update_data}
                    )
            except Exception as e:
                error_msg = str(e)
                # If it's a duplicate key error, try with a new product_id
                if "E11000" in error_msg or "duplicate key" in error_msg.lower():
                    try:
                        import hashlib
                        url_hash = hashlib.md5(
                            f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                        ).hexdigest()
                        product["product_id"] = int(url_hash[:8], 16)
                        products_collection.insert_one(product)
                        stored_count += 1
                        logger.info(f"Retried insert with new product_id for {product.get('product_url')}")
                    except Exception as retry_error:
                        logger.error(f"Error storing product (retry failed): {retry_error}")
                        scraper.errors.append(f"Storage error: {str(retry_error)}")
                else:
                    logger.error(f"Error storing product: {e}")
                    scraper.errors.append(f"Storage error: {error_msg}")
        
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



