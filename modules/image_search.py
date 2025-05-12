import re
import time
import requests
from typing import List, Dict, Any, Optional, Union, Tuple

def get_html_content(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Get HTML content from a URL"""
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return None

def get_images_from_bing(query: str) -> List[Dict[str, str]]:
    """Search for images using Bing search engine"""
    try:
        # Set up the headers for the request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # Construct search URL
        search_url = f"https://www.bing.com/images/search?q={query}&first=1"
        
        # Get the HTML content of the search results page
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            print(f"Failed to get HTML content from Bing for query: {query}")
            return []
        
        # Extract image URLs using regex
        img_urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html_content)
        
        if not img_urls or len(img_urls) == 0:
            print(f"No image URLs found from Bing for query: {query}")
            return []
        
        # Create image objects from the URLs (up to 5 images)
        images = []
        for i, url in enumerate(img_urls[:5]):
            images.append({
                "url": url,
                "title": f"{query} image {i+1}",
                "source": "Bing"
            })
        
        print(f"Successfully found {len(images)} images from Bing for query: {query}")
        return images
    
    except Exception as e:
        print(f"Error in get_images_from_bing for query '{query}': {str(e)}")
        return []

def get_images_from_yahoo(query: str) -> List[Dict[str, str]]:
    """Search for images using Yahoo search engine"""
    try:
        # Set up the headers for the request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # Construct search URL
        search_url = f"https://images.search.yahoo.com/search/images?p={query}"
        
        # Get the HTML content of the search results page
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            print(f"Failed to get HTML content from Yahoo for query: {query}")
            return []
        
        # Extract image URLs using regex - adapt this regex pattern for Yahoo's HTML structure
        img_urls = re.findall(r'<img[^>]+src="([^"]+)"[^>]*class="process[^>]*>', html_content)
        
        if not img_urls or len(img_urls) == 0:
            # Try alternative pattern
            img_urls = re.findall(r'<img[^>]+data-src="([^"]+)"[^>]*class="process[^>]*>', html_content)
        
        if not img_urls or len(img_urls) == 0:
            # Try another alternative pattern
            img_urls = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', html_content)
            # Filter out small images and icons
            img_urls = [url for url in img_urls if not ('icon' in url.lower() or 'logo' in url.lower())]
            
        if not img_urls or len(img_urls) == 0:
            print(f"No image URLs found from Yahoo for query: {query}")
            return []
        
        # Create image objects from the URLs (up to 5 images)
        images = []
        for i, url in enumerate(img_urls[:5]):
            images.append({
                "url": url,
                "title": f"{query} image {i+1}",
                "source": "Yahoo"
            })
        
        print(f"Successfully found {len(images)} images from Yahoo for query: {query}")
        return images
    
    except Exception as e:
        print(f"Error in get_images_from_yahoo for query '{query}': {str(e)}")
        return []

def is_valid_image_url(url: str) -> bool:
    """
    Validate if a URL points to a valid image
    
    Args:
        url: The URL to validate
        
    Returns:
        True if the URL points to a valid image, False otherwise
    """
    # Cache for validated URLs to avoid checking the same URL multiple times
    if not hasattr(is_valid_image_url, 'cache'):
        is_valid_image_url.cache = {}
    
    # Return cached result if available
    if url in is_valid_image_url.cache:
        return is_valid_image_url.cache[url]
    
    try:
        # Check if URL format is valid (fast check)
        if not url or not url.startswith(('http://', 'https://')):
            is_valid_image_url.cache[url] = False
            return False
        
        # Quick reject for common problematic patterns (fast check)
        lower_url = url.lower()
        
        # Avoid obviously small or problematic image formats
        if any(ext in lower_url for ext in ['.gif', '.svg', '.webp', '.ico', '.icon']):
            is_valid_image_url.cache[url] = False
            return False
            
        # Avoid common placeholder/icon paths - these are typically not good as article images
        bad_patterns = ['icon', 'placeholder', 'blank', 'transparent', 'logo', 'button', 
                        'favicon', 'pixel.', 'spacer', 'spinner', 'loading', '1x1', 
                        'avatar', 'profile-pic']
        
        if any(pattern in lower_url for pattern in bad_patterns):
            is_valid_image_url.cache[url] = False
            return False
        
        # Accept common reliable image domains without full validation (fast path)
        reliable_domains = [
            'cdn.pixabay.com', 
            'images.unsplash.com',
            'img.freepik.com',
            'upload.wikimedia.org',
            'i.pinimg.com',
            'cdn.statically.io',
            'upload.wikimedia.org'
        ]
        
        if any(domain in lower_url for domain in reliable_domains):
            # Additional check for acceptable file paths
            if any(ext in lower_url for ext in ['.jpg', '.jpeg', '.png']):
                is_valid_image_url.cache[url] = True
                return True
        
        # Make a HEAD request with short timeout (faster than GET request)
        response = requests.head(url, timeout=3, allow_redirects=True)
        
        # Check if response is successful 
        if response.status_code != 200:
            is_valid_image_url.cache[url] = False
            return False
            
        # Check Content-Type header
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            is_valid_image_url.cache[url] = False
            return False
        
        # Check Content-Length if available (faster than downloading)
        content_length = response.headers.get('Content-Length')
        if content_length and content_length.isdigit():
            if int(content_length) < 8192:  # 8KB minimum
                is_valid_image_url.cache[url] = False
                return False
        else:
            # If size can't be determined from header, do a partial GET
            try:
                # Request only first 8KB to check if size is reasonable
                response = requests.get(url, timeout=3, stream=True, headers={'Range': 'bytes=0-8191'})
                content = next(response.iter_content(8192))
                if len(content) < 8192:  # If less than 8KB, it's likely too small
                    is_valid_image_url.cache[url] = False
                    return False
                response.close()
            except Exception:
                # If streaming fails, accept the image anyway if other checks passed
                pass
            
        # All checks passed
        is_valid_image_url.cache[url] = True
        return True
        
    except Exception as e:
        # On any error, assume URL is invalid
        is_valid_image_url.cache[url] = False
        return False

def get_images(query: str) -> List[Dict[str, str]]:
    """
    Get valid images from multiple sources with enhanced validation
    
    Args:
        query: The search query
        
    Returns:
        List of image objects with URL, title, and source
    """
    print(f"Searching for images with query: {query}")
    
    # Try Bing first
    bing_images = get_images_from_bing(query)
    
    # Filter for valid images
    valid_bing_images = []
    for img in bing_images:
        if is_valid_image_url(img['url']):
            valid_bing_images.append(img)
            print(f"✓ Valid image found from Bing: {img['url'][:60]}...")
        else:
            print(f"✗ Invalid image skipped from Bing: {img['url'][:60]}...")
    
    # If Bing returned enough valid images, use them
    if len(valid_bing_images) >= 3:
        return valid_bing_images
    
    # Otherwise, try Yahoo
    yahoo_images = get_images_from_yahoo(query)
    
    # Filter Yahoo images for validity
    valid_yahoo_images = []
    for img in yahoo_images:
        if is_valid_image_url(img['url']):
            valid_yahoo_images.append(img)
            print(f"✓ Valid image found from Yahoo: {img['url'][:60]}...")
        else:
            print(f"✗ Invalid image skipped from Yahoo: {img['url'][:60]}...")
    
    # Combine the valid results
    all_valid_images = valid_bing_images + valid_yahoo_images
    
    # If we still don't have enough images, try with different queries
    if len(all_valid_images) < 2:
        # Try several alternative queries
        alternative_queries = [
            ' '.join(query.split()[:3]),  # First 3 words
            query + " high quality image",
            query + " featured image",
            ' '.join(query.split()[:2]) + " guide image"
        ]
        
        for alt_query in alternative_queries:
            if len(all_valid_images) >= 3:
                break
                
            print(f"Trying alternative query: {alt_query}")
            
            # Try Bing with alternative query
            alt_bing_images = get_images_from_bing(alt_query)
            for img in alt_bing_images:
                if is_valid_image_url(img['url']):
                    all_valid_images.append(img)
                    print(f"✓ Valid image found from alternative query: {img['url'][:60]}...")
                    if len(all_valid_images) >= 5:  # Cap at 5 images
                        break
    
    print(f"Total valid images found: {len(all_valid_images)}")
    return all_valid_images