import re
from typing import List, Optional

def generate_tags_from_title(title: str, subject: str) -> List[str]:
    """
    Generate SEO-optimized tags from the title and subject of the article
    
    Args:
        title: The article title
        subject: The article subject/keyword
        
    Returns:
        List of generated tags
    """
    # Common words to exclude (both English and Indonesian)
    stop_words = [
        'yang', 'untuk', 'dengan', 'adalah', 'dari', 'cara', 'tips', 'trik',
        'dan', 'atau', 'jika', 'maka', 'namun', 'tetapi', 'juga', 'oleh',
        'the', 'and', 'that', 'this', 'with', 'for', 'from', 'how', 'what',
        'when', 'why', 'where', 'who', 'will', 'your', 'their', 'our', 'its'
    ]
    
    # Clean and normalize text
    clean_title = title.lower().replace(':', ' ').replace('-', ' ').replace(',', ' ').replace('.', ' ')
    clean_subject = subject.lower()
    
    # Extract potential multi-word phrases from title (2-3 words)
    title_parts = clean_title.split()
    title_phrases = []
    
    # Get 2-word phrases
    for i in range(len(title_parts) - 1):
        phrase = title_parts[i] + ' ' + title_parts[i + 1]
        if all(word not in stop_words for word in phrase.split()):
            title_phrases.append(phrase)
    
    # Get 3-word phrases
    for i in range(len(title_parts) - 2):
        phrase = title_parts[i] + ' ' + title_parts[i + 1] + ' ' + title_parts[i + 2]
        if all(word not in stop_words for word in phrase.split()):
            title_phrases.append(phrase)
    
    # Get single words from title
    title_words = [word.strip() for word in clean_title.split() 
                 if len(word.strip()) > 3 and word.lower() not in stop_words]
    
    # Get words from subject
    subject_words = [word.strip() for word in clean_subject.split() 
                    if len(word.strip()) > 3 and word.lower() not in stop_words]
    
    # Build final tag list prioritizing multi-word phrases
    all_tags = []
    
    # First add any 3-word phrases (usually most specific)
    three_word_phrases = [p for p in title_phrases if len(p.split()) == 3]
    all_tags.extend(three_word_phrases[:2])  # Up to 2 three-word phrases
    
    # Then add 2-word phrases
    two_word_phrases = [p for p in title_phrases if len(p.split()) == 2]
    all_tags.extend(two_word_phrases[:2])  # Up to 2 two-word phrases
    
    # Then add important single words
    remaining_slots = 5 - len(all_tags)
    if remaining_slots > 0:
        # Combine and remove duplicates (words already in phrases)
        single_words = []
        for word in title_words + subject_words:
            already_included = any(word in phrase for phrase in all_tags)
            if not already_included and word not in single_words:
                single_words.append(word)
        
        all_tags.extend(single_words[:remaining_slots])
    
    # Ensure we don't exceed 5 tags and we have at least 1 tag
    return all_tags[:5] if all_tags else [subject.split()[0]]

def extract_featured_image(article_content: str) -> Optional[str]:
    """
    Extract the first image URL from the article content to use as featured image
    
    Args:
        article_content: The article content with potential image URLs
        
    Returns:
        The first image URL found, or None if no image is found
    """
    # Look for markdown image pattern ![alt text](image_url)
    image_pattern = r'!\[.*?\]\((.*?)\)'
    image_matches = re.findall(image_pattern, article_content)
    
    if image_matches:
        return image_matches[0]  # Return the first image URL found
    
    # Look for HTML image pattern <img src="image_url" ... >
    html_pattern = r'<img.*?src=["\'](.*?)["\'].*?>'
    html_matches = re.findall(html_pattern, article_content)
    
    if html_matches:
        return html_matches[0]  # Return the first image URL found
    
    return None  # No image found

def optimize_title_for_seo(title: str, max_length: int = 60) -> str:
    """
    Optimize a title for SEO by keeping it under a specified length
    
    Args:
        title: The original title
        max_length: Maximum length (60 characters is optimal for search engines)
        
    Returns:
        The optimized title
    """
    if len(title) <= max_length:
        return title
    
    # Try to find a good cutoff point
    cutoff = max_length
    while cutoff > 0 and title[cutoff] not in (' ', '-', ':', ',', '.'):
        cutoff -= 1
    
    if cutoff == 0:
        # If no good cutoff point found, just use max_length
        return title[:max_length] + '...'
    else:
        return title[:cutoff] + '...'

def calculate_keyword_density(text: str, keyword: str) -> float:
    """
    Calculate keyword density in a text
    
    Args:
        text: The text to analyze
        keyword: The keyword to count
        
    Returns:
        Keyword density as a percentage
    """
    # Count total words
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Count keyword occurrences (case insensitive)
    keyword_count = text.lower().count(keyword.lower())
    
    # Calculate density as percentage
    return (keyword_count / total_words) * 100

def get_seo_recommendations(title: str, content: str, keyword: str) -> List[str]:
    """
    Generate SEO recommendations for the article
    
    Args:
        title: The article title
        content: The article content
        keyword: The target keyword
        
    Returns:
        List of SEO recommendations
    """
    recommendations = []
    
    # Check title length
    if len(title) > 60:
        recommendations.append("Title is too long. Consider shortening it to under 60 characters.")
    
    # Check if keyword is in title
    if keyword.lower() not in title.lower():
        recommendations.append(f"Add the keyword '{keyword}' to the title.")
    
    # Check content length
    word_count = len(content.split())
    if word_count < 1000:
        recommendations.append(f"Content is too short ({word_count} words). Aim for at least 1000 words.")
    
    # Check keyword density
    density = calculate_keyword_density(content, keyword)
    if density < 0.5:
        recommendations.append(f"Keyword density is too low ({density:.1f}%). Aim for 1-2%.")
    elif density > 3:
        recommendations.append(f"Keyword density is too high ({density:.1f}%). Aim for 1-2% to avoid keyword stuffing.")
    
    # Check headings
    if "##" not in content:
        recommendations.append("Add H2 headings to structure your content.")
    
    # Check for images
    if "![" not in content and "<img" not in content:
        recommendations.append("Add images to make your content more engaging.")
    
    return recommendations