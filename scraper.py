#!/usr/bin/env python3
"""
PagesJaunes.ca Business Contact Scraper
Scrapes business contact information from PagesJaunes.ca and exports to CSV
Updated version with improved selectors, duplicate handling, and PagesJaunes.ca website extraction
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
from urllib.parse import urljoin, urlparse, unquote
import argparse
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PagesJaunesScraper:
    def __init__(self, max_pages=5, delay_range=(1, 3), debug=False):
        self.max_pages = max_pages
        self.delay_range = delay_range
        self.debug = debug
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        self.email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        
    def get_random_headers(self):
        """Return random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def safe_request(self, url, timeout=15, max_retries=3):
        """Make a safe HTTP request with retries"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                response = self.session.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                
                if self.debug:
                    logger.debug(f"Successfully fetched {url} (Status: {response.status_code})")
                
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def search_pagesjaunes(self, query, location=""):
        """Search PagesJaunes.ca for businesses"""
        businesses = []
        seen_businesses = set()  # To avoid duplicates
        
        for page in range(1, self.max_pages + 1):
            logger.info(f"Searching page {page} for '{query}'...")
            
            # Construct search URL - Updated for current PagesJaunes.ca structure
            if location:
                search_url = f"https://www.pagesjaunes.ca/search/si/{page}/{query}/{location}"
            else:
                search_url = f"https://www.pagesjaunes.ca/search/si/{page}/{query}"
            
            if self.debug:
                logger.debug(f"Fetching URL: {search_url}")
            
            response = self.safe_request(search_url)
            if not response:
                logger.warning(f"Failed to fetch page {page}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if self.debug:
                # Save HTML for debugging
                with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.debug(f"Saved debug HTML to debug_page_{page}.html")
            
            # Multiple selectors for business listings - Updated for 2025
            listings = self.find_business_listings(soup)
            
            if not listings:
                logger.warning(f"No listings found on page {page}")
                if self.debug:
                    logger.debug("Available div classes on page:")
                    for div in soup.find_all('div', class_=True)[:10]:
                        logger.debug(f"  - {div.get('class')}")
                break
                
            page_businesses = 0
            for listing in listings:
                business = self.extract_business_info(listing)
                if business:
                    # Create unique identifier to avoid duplicates
                    business_id = f"{business['company_name']}_{business['phone']}"
                    if business_id not in seen_businesses:
                        businesses.append(business)
                        seen_businesses.add(business_id)
                        page_businesses += 1
            
            logger.info(f"Found {page_businesses} unique businesses on page {page}")
            
            # Check if we should continue to next page
            if page_businesses == 0:
                logger.info("No new businesses found, stopping pagination")
                break
            
            # Random delay between pages
            time.sleep(random.uniform(*self.delay_range))
        
        logger.info(f"Total unique businesses found: {len(businesses)}")
        return businesses
    
    def find_business_listings(self, soup):
        """Find business listings using multiple selector strategies"""
        # Try different selector patterns that PagesJaunes.ca might use
        selectors = [
            # Modern selectors
            'div[data-yext-id]',
            'div[data-business-id]',
            'div.listing',
            'div.search-results__item',
            'div.result-item',
            'div.business-result',
            'article.listing',
            'div.merchant',
            'div.business-listing',
            
            # Generic patterns
            'div[class*="listing"]',
            'div[class*="business"]',
            'div[class*="result"]',
            'div[class*="merchant"]',
            'li[class*="listing"]',
            'li[class*="business"]',
            
            # Fallback to any div with business-like content
            'div:has(a[href*="/bus/"])',
        ]
        
        for selector in selectors:
            listings = soup.select(selector)
            if listings:
                logger.info(f"Found {len(listings)} listings using selector: {selector}")
                return listings
        
        # If no specific selectors work, try to find divs containing business links
        business_links = soup.find_all('a', href=re.compile(r'/bus/'))
        if business_links:
            logger.info(f"Found {len(business_links)} business links, extracting parent containers")
            listings = []
            for link in business_links:
                # Get the parent container that likely contains all business info
                parent = link.find_parent('div')
                if parent and parent not in listings:
                    listings.append(parent)
            return listings
        
        return []
    
    def extract_business_info(self, listing):
        """Extract business information from a listing - Updated selectors"""
        try:
            business = {
                'company_name': '',
                'phone': '',
                'website': '',
                'email': ''
            }
            
            if self.debug:
                logger.debug(f"Processing listing: {listing.get('class', 'No class')}")
            
            # Extract company name - Multiple strategies
            business['company_name'] = self.extract_company_name(listing)
            
            # Extract phone number - Multiple strategies
            business['phone'] = self.extract_phone_number(listing)
            
            # Extract website - Multiple strategies including PagesJaunes.ca redirects
            business['website'] = self.extract_website(listing)
            
            # Only return business if we have at least name
            if business['company_name']:
                if self.debug:
                    logger.debug(f"Extracted business: {business}")
                return business
            else:
                if self.debug:
                    logger.debug("No company name found, skipping listing")
                
        except Exception as e:
            logger.warning(f"Error extracting business info: {e}")
            if self.debug:
                logger.debug(f"Listing HTML: {listing}")
        
        return None
    
    def extract_company_name(self, listing):
        """Extract company name using multiple strategies"""
        name_selectors = [
            # Direct selectors for business name
            'h2 a', 'h3 a', 'h4 a',
            '.business-name a', '.merchant-name a', '.listing-name a',
            '.title a', '.name a',
            'a[href*="/bus/"]',
            
            # Text-only selectors
            'h2', 'h3', 'h4',
            '.business-name', '.merchant-name', '.listing-name',
            '.title', '.name',
            
            # Data attributes
            '[data-business-name]',
            '[data-merchant-name]',
        ]
        
        for selector in name_selectors:
            elem = listing.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 1:  # Must be more than 1 character
                    return name
                    
        return ""
    
    def extract_phone_number(self, listing):
        """Extract phone number using multiple strategies"""
        phone_selectors = [
            # Direct phone selectors
            '.phone', '.telephone', '.tel',
            '.contact-phone', '.business-phone',
            '[data-phone]', '[data-telephone]',
            'a[href^="tel:"]',
            
            # Generic selectors that might contain phone
            '.contact-info', '.contact-details'
        ]
        
        # First try specific selectors
        for selector in phone_selectors:
            elem = listing.select_one(selector)
            if elem:
                phone_text = ""
                
                # Check different sources for phone number
                if elem.get('href') and 'tel:' in elem.get('href'):
                    phone_text = elem.get('href').replace('tel:', '')
                elif elem.get('data-phone'):
                    phone_text = elem.get('data-phone')
                elif elem.get('data-telephone'):
                    phone_text = elem.get('data-telephone')
                else:
                    phone_text = elem.get_text(strip=True)
                
                # Clean and validate phone number
                phone_clean = self.clean_phone_number(phone_text)
                if phone_clean:
                    return phone_clean
        
        # Fallback: search for phone patterns in all text
        all_text = listing.get_text()
        phone_match = self.phone_pattern.search(all_text)
        if phone_match:
            return self.clean_phone_number(phone_match.group())
        
        return ""
    
    def clean_phone_number(self, phone_text):
        """Clean and format phone number"""
        if not phone_text:
            return ""
        
        # Remove common non-phone text
        if any(word in phone_text.lower() for word in ['email', 'site', 'web', 'www', 'http']):
            return ""
        
        # Extract digits and formatting
        phone_match = self.phone_pattern.search(phone_text)
        if phone_match:
            return phone_match.group().strip()
        
        # If no regex match, try to clean manually
        digits_only = re.sub(r'[^\d]', '', phone_text)
        if len(digits_only) == 10:
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"1-({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        
        return ""
    
    def extract_website(self, listing):
        """Extract website URL using multiple strategies including PagesJaunes.ca redirects"""
        
        # Strategy 1: PagesJaunes.ca specific redirect links
        pj_redirect_links = listing.find_all('a', href=re.compile(r'/gourl/.*redirect='))
        for link in pj_redirect_links:
            href = link.get('href')
            if href and 'redirect=' in href:
                try:
                    # Extract the redirect parameter
                    redirect_param = href.split('redirect=')[1].split('&')[0]
                    # URL decode the website
                    decoded_website = unquote(redirect_param)
                    
                    if self.debug:
                        logger.debug(f"Found PJ redirect link: {href}")
                        logger.debug(f"Decoded website: {decoded_website}")
                    
                    # Validate the URL
                    if decoded_website.startswith(('http://', 'https://')):
                        return decoded_website
                    elif decoded_website.startswith('www.'):
                        return f"https://{decoded_website}"
                    elif '.' in decoded_website and not decoded_website.startswith('/'):
                        return f"https://{decoded_website}"
                        
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Error processing redirect link: {e}")
                    continue
        
        # Strategy 2: Direct website links with specific PagesJaunes.ca selectors
        pj_website_selectors = [
            '.mlr__item--website a',
            '.mlritem--website a',
            'li[class*="website"] a',
            'li[class*="site"] a'
        ]
        
        for selector in pj_website_selectors:
            elem = listing.select_one(selector)
            if elem:
                href = elem.get('href')
                if href and '/gourl/' in href and 'redirect=' in href:
                    try:
                        redirect_param = href.split('redirect=')[1].split('&')[0]
                        decoded_website = unquote(redirect_param)
                        
                        if self.debug:
                            logger.debug(f"Found PJ website selector: {selector}")
                            logger.debug(f"Decoded website: {decoded_website}")
                        
                        if decoded_website.startswith(('http://', 'https://')):
                            return decoded_website
                        elif decoded_website.startswith('www.'):
                            return f"https://{decoded_website}"
                            
                    except Exception as e:
                        if self.debug:
                            logger.debug(f"Error processing website selector: {e}")
                        continue
        
        # Strategy 3: Generic website selectors
        website_selectors = [
            '.website a', '.site a', '.web a',
            '.business-website a', '.merchant-website a',
            'a[href^="http"]:not([href*="pagesjaunes"]):not([href*="tel:"]):not([href*="mailto:"])',
            '[data-website]', '[data-url]'
        ]
        
        for selector in website_selectors:
            elem = listing.select_one(selector)
            if elem:
                href = elem.get('href') or elem.get('data-website') or elem.get('data-url')
                if href and href.startswith('http') and 'pagesjaunes' not in href.lower():
                    return href
        
        # Strategy 4: Search for any HTTP links in the listing text
        all_links = listing.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if (href and 
                href.startswith(('http://', 'https://')) and 
                'pagesjaunes' not in href.lower() and 
                'tel:' not in href and 
                'mailto:' not in href):
                
                # Additional filtering for common non-website links
                if not any(x in href.lower() for x in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com']):
                    return href
        
        if self.debug:
            logger.debug("No website found for this listing")
        
        return ""
    
    def extract_email_from_website(self, website_url):
        """Extract email address from a website"""
        try:
            logger.info(f"Checking website: {website_url}")
            response = self.safe_request(website_url, timeout=15)
            
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for mailto links first (most reliable)
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link.get('href').replace('mailto:', '').split('?')[0].split('&')[0]
                if self.email_pattern.match(email):
                    return email
            
            # Search for email patterns in text content
            page_text = soup.get_text()
            emails = self.email_pattern.findall(page_text)
            
            if emails:
                # Filter out common false positives
                valid_emails = []
                for email in emails:
                    email_lower = email.lower()
                    # Skip common false positives
                    if not any(skip in email_lower for skip in [
                        'example.com', 'test.com', 'sample.com', 'placeholder',
                        '.png', '.jpg', '.gif', '.css', '.js', '.pdf',
                        'noreply', 'no-reply', 'donotreply'
                    ]):
                        valid_emails.append(email)
                
                if valid_emails:
                    return valid_emails[0]  # Return first valid email
                        
        except Exception as e:
            logger.warning(f"Error extracting email from {website_url}: {e}")
        
        return None
    
    def scrape_businesses(self, query, location=""):
        """Main method to scrape businesses"""
        logger.info(f"Starting scrape for query: '{query}' in location: '{location}'")
        
        # Search for businesses
        businesses = self.search_pagesjaunes(query, location)
        
        if not businesses:
            logger.error("No businesses found!")
            return []
        
        # Extract emails from websites
        businesses_with_websites = [b for b in businesses if b['website']]
        if businesses_with_websites:
            logger.info(f"Extracting email addresses from {len(businesses_with_websites)} websites...")
            
            for i, business in enumerate(businesses_with_websites, 1):
                logger.info(f"Processing business {i}/{len(businesses_with_websites)}: {business['company_name']}")
                
                email = self.extract_email_from_website(business['website'])
                if email:
                    business['email'] = email
                    logger.info(f"Found email: {email}")
                
                # Delay between website requests
                time.sleep(random.uniform(1, 2))
        else:
            logger.info("No businesses with websites found, skipping email extraction")
        
        return businesses
    
    def save_to_csv(self, businesses, filename):
        """Save businesses to CSV file"""
        if not businesses:
            logger.error("No businesses to save!")
            return
        
        df = pd.DataFrame(businesses)
        
        # Reorder columns
        column_order = ['company_name', 'phone', 'website', 'email']
        df = df.reindex(columns=column_order)
        
        # Rename columns for better readability
        df.columns = ['Company Name', 'Phone Number', 'Website URL', 'Email Address']
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(businesses)} businesses to {filename}")
        
        # Print summary
        print(f"\n📊 SCRAPING SUMMARY")
        print(f"=" * 50)
        print(f"Total businesses found: {len(businesses)}")
        print(f"Businesses with phone numbers: {sum(1 for b in businesses if b['phone'])}")
        print(f"Businesses with websites: {sum(1 for b in businesses if b['website'])}")
        print(f"Businesses with emails: {sum(1 for b in businesses if b['email'])}")
        print(f"Results saved to: {filename}")

def create_filename(query):
    """Create a safe filename from search query"""
    # Remove special characters and replace spaces with underscores
    safe_name = re.sub(r'[^\w\s-]', '', query.lower())
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{safe_name}.csv"

def main():
    parser = argparse.ArgumentParser(description='Scrape business contact info from PagesJaunes.ca')
    parser.add_argument('--query', '-q', help='Search query (e.g., "Avocat")')
    parser.add_argument('--location', '-l', default='', help='Location filter (e.g., "Terrebonne")')
    parser.add_argument('--pages', '-p', type=int, default=5, help='Number of pages to scrape (default: 5)')
    parser.add_argument('--output', '-o', help='Output filename (optional)')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Get search query
    if args.query:
        query = args.query
    else:
        query = input("Enter search term (e.g., 'Avocat'): ").strip()
    
    if not query:
        print("Error: Search query is required!")
        sys.exit(1)
    
    # Get location if not provided
    if not args.location:
        location = input("Enter location (optional, press Enter to skip): ").strip()
    else:
        location = args.location
    
    # Create output filename
    if args.output:
        output_file = args.output
    else:
        output_file = create_filename(f"{query}_{location}" if location else query)
    
    print(f"\n🔍 Searching for: '{query}'")
    if location:
        print(f"📍 Location: '{location}'")
    print(f"📄 Output file: '{output_file}'")
    print(f"📖 Pages to scrape: {args.pages}")
    if args.debug:
        print("🐛 Debug mode: ENABLED")
    print("-" * 50)
    
    # Initialize scraper
    scraper = PagesJaunesScraper(max_pages=args.pages, debug=args.debug)
    
    try:
        # Scrape businesses
        businesses = scraper.scrape_businesses(query, location)
        
        if businesses:
            # Save to CSV
            scraper.save_to_csv(businesses, output_file)
            
            # Show sample results
            print("\n📋 SAMPLE RESULTS:")
            print("-" * 50)
            for i, business in enumerate(businesses[:5], 1):
                print(f"{i}. {business['company_name']}")
                print(f"   Phone: {business['phone'] or 'N/A'}")
                print(f"   Website: {business['website'] or 'N/A'}")
                print(f"   Email: {business['email'] or 'N/A'}")
                print()
                
            if len(businesses) > 5:
                print(f"... and {len(businesses) - 5} more businesses")
        else:
            print("❌ No businesses found for your search query.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
