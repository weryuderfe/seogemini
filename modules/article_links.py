import os
import json
import datetime
from typing import List, Dict, Any, Optional, Set, Union

# Constants
ARTICLE_LINKS_FILE = "article_links.json"

class ArticleLinksManager:
    """Class to manage article links for internal linking"""
    
    def __init__(self, filename: str = ARTICLE_LINKS_FILE):
        """Initialize with the path to the article links file"""
        self.filename = filename
        self.articles = self._load_articles()
    
    def _load_articles(self) -> List[Dict[str, str]]:
        """Load articles from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except:
                return []
        return []
    
    def save_articles(self) -> None:
        """Save articles to JSON file"""
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.articles, file, ensure_ascii=False, indent=2)
    
    def add_article(self, title: str, subject: str, permalink: str) -> bool:
        """
        Add a new article to the link database
        
        Args:
            title: The article title
            subject: The article subject/keyword
            permalink: The article permalink
            
        Returns:
            True if article added successfully, False if already exists
        """
        # Check if article with this permalink already exists
        for article in self.articles:
            if article['permalink'] == permalink:
                return False
        
        # Add new article
        self.articles.append({
            'title': title,
            'subject': subject,
            'permalink': permalink,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Save to file
        self.save_articles()
        return True
    
    def get_related_articles(self, subject: str, current_permalink: str, max_links: int = 3) -> List[Dict[str, str]]:
        """
        Get related articles based on subject relevance
        
        Args:
            subject: The subject to find related articles for
            current_permalink: The current article's permalink (to exclude it from results)
            max_links: Maximum number of related articles to return
            
        Returns:
            List of related article dicts with title and permalink
        """
        # Get words from the subject
        subject_words = set(subject.lower().split())
        
        # Score articles based on relevance
        scored_articles = []
        for article in self.articles:
            # Skip the current article
            if article['permalink'] == current_permalink:
                continue
            
            # Calculate word overlap for relevance
            article_subject_words = set(article['subject'].lower().split())
            overlap = len(subject_words.intersection(article_subject_words))
            
            if overlap > 0:
                scored_articles.append({
                    'title': article['title'],
                    'permalink': article['permalink'],
                    'score': overlap
                })
        
        # Sort by relevance score (higher is more relevant)
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        
        # Return the top N most relevant articles
        return scored_articles[:max_links]
    
    def get_all_articles(self) -> List[Dict[str, str]]:
        """Get all articles in the database"""
        return self.articles
    
    def get_article_by_permalink(self, permalink: str) -> Optional[Dict[str, str]]:
        """Get an article by its permalink"""
        for article in self.articles:
            if article['permalink'] == permalink:
                return article
        return None
    
    def delete_article(self, permalink: str) -> bool:
        """Delete an article by its permalink"""
        for i, article in enumerate(self.articles):
            if article['permalink'] == permalink:
                del self.articles[i]
                self.save_articles()
                return True
        return False
    
    def update_article(self, permalink: str, new_data: Dict[str, str]) -> bool:
        """Update an article's data"""
        for i, article in enumerate(self.articles):
            if article['permalink'] == permalink:
                # Update allowed fields
                if 'title' in new_data:
                    article['title'] = new_data['title']
                if 'subject' in new_data:
                    article['subject'] = new_data['subject']
                
                # Save changes
                self.save_articles()
                return True
        return False
    
    def get_articles_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get articles by category (derived from first word of subject)"""
        result = []
        for article in self.articles:
            subject = article.get('subject', '')
            article_category = subject.split()[0] if subject.split() else ''
            
            if article_category.lower() == category.lower():
                result.append(article)
        
        return result
    
    def get_article_statistics(self) -> Dict[str, Any]:
        """Get statistics about articles"""
        total = len(self.articles)
        
        # Count categories
        categories = {}
        for article in self.articles:
            subject = article.get('subject', '')
            category = subject.split()[0] if subject.split() else 'uncategorized'
            
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        # Get dates
        dates = []
        for article in self.articles:
            if 'timestamp' in article:
                try:
                    date = datetime.datetime.fromisoformat(article['timestamp']).strftime('%Y-%m-%d')
                    dates.append(date)
                except:
                    pass
        
        # Count by date
        dates_count = {}
        for date in dates:
            if date in dates_count:
                dates_count[date] += 1
            else:
                dates_count[date] = 1
        
        return {
            'total': total,
            'categories': categories,
            'dates': dates_count
        }