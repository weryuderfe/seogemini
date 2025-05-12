import os
import re
import time
import json
from datetime import datetime
from slugify import slugify
from typing import Dict, List, Any, Optional, Union

# Import other modules
from modules.api_client import get_gemini_client
from modules.image_search import get_images, is_valid_image_url
from modules.article_links import ArticleLinksManager
from modules.language_utils import detect_language

# Initialize article links manager
article_links_manager = ArticleLinksManager()

def generate_title(subject: str, language: str, model: str = "gemini-1.5-flash") -> str:
    """Generate a catchy and SEO-optimized title for an article"""
    
    # Create prompt for title generation
    title_prompt = (
        f"Write a catchy and SEO-optimized article title in {language} about '{subject}'.\n\n"
        f"RULES:\n"
        f"1. Make it attention-grabbing and click-worthy without being clickbait\n"
        f"2. Include the main keyword \"{subject}\" or a closely related term\n"
        f"3. Keep it under 60 characters if possible\n"
        f"4. Make sure it's in {language} language\n"
        f"5. Add a subtitle separated by a colon or dash if appropriate\n"
        f"6. Do not include unnecessary punctuation or all caps\n"
        f"7. If the language is English, make the title more professional and concise\n"
        f"8. For English titles, use power words that drive engagement and clicks\n\n"
        f"FORMAT THE TITLE EXACTLY LIKE THIS (no extra text): Title Here"
    )
    
    try:
        # Get the Gemini client
        client = get_gemini_client()
        
        # Generate title via API request
        response = client.generate_content(title_prompt, model)
        
        if not response:
            return f"Article About {subject}"
        
        # Clean up title (remove quotes but preserve meaningful ones like apostrophes)
        title = response.strip().replace('"', '')
        
        # Handle multi-paragraph responses (take only the first line)
        title = title.split('\n')[0]
        
        return title
            
    except Exception as e:
        print(f"\nError generating title: {str(e)}")
        # Fallback to a simple title
        return f"Article About {subject}"

def generate_article(title: str, subject: str, domain: str, permalink: str, 
                    language: str, model: str = "gemini-1.5-flash", 
                    related_articles: Optional[List[Dict[str, str]]] = None) -> str:
    """Generate a full SEO-optimized article"""
    
    # Add related articles information to prompt if available
    related_links_text = ""
    if related_articles and len(related_articles) > 0:
        related_links_text = "RELATED ARTICLES TO INCLUDE:\n"
        for i, article in enumerate(related_articles):
            related_links_text += f"{i+1}. Title: \"{article['title']}\", Link: {domain}{article['permalink']}\n"
        related_links_text += "Include these links naturally within the article content using relevant anchor text that relates to both the keyword and the destination article.\n\n"
    
    # Determine if we should force English content based on subject or language
    force_english = language.lower() == "english" or any(eng_term in subject.lower() for eng_term in ["seo", "digital marketing", "google", "content marketing", "social media", "analytics"])
    
    # Define article language requirements
    language_specific_instructions = ""
    if force_english:
        language_specific_instructions = (
            "ENGLISH CONTENT REQUIREMENTS:\n"
            "1. Write the entire article in professional, flawless English regardless of the keyword language.\n"
            "2. Use precise terminology and industry-standard vocabulary.\n"
            "3. Maintain a clear, authoritative tone that conveys expertise.\n"
            "4. For technical topics, use proper technical terms and explain them clearly.\n"
            "5. Use American English spelling and grammar conventions.\n\n"
        )
    
    # Create the article generation prompt
    article_prompt = (
        f"Write an extremely comprehensive and in-depth SEO-optimized article for the following title: \"{title}\"\n\n"
        f"FORMAT REQUIREMENTS:\n"
        f"1. Start with an engaging 3-4 paragraph introduction that includes the domain name '{domain}' as a BOLD HYPERLINK only ONCE in the first paragraph. Format it as [**{domain}**](https://{domain}). This automatically creates both bold and hyperlink.\n"
        f"2. Immediately after the introduction, insert an image placeholder with format: [IMAGE: {subject} overview infographic].\n"
        f"3. Create a deep hierarchical structure with H2, H3, and H4 headings (use markdown format: ##, ###, ####). START with H2 headings after the introduction, and use H3 and H4 for more detailed subsections.\n"
        f"4. Create a minimum of 4000 words (target range: 4000-7000 words) with detailed professional-level analysis for each heading section.\n"
        f"5. Bold 5-7 primary and secondary keywords related to '{subject}' throughout the article for SEO optimization. These should appear naturally in the text, especially at the beginning of paragraphs.\n"
        f"6. Include exactly 6-7 image placeholders throughout the article using format: [IMAGE: detailed description related to the heading], but ALWAYS place these image placeholders BEFORE their related headings, not after.\n"
        f"7. DO NOT include any image placeholders in the conclusion section or at the very end of the article.\n" 
        f"8. End with a warm, personalized conclusion paragraph that directly addresses the reader, followed by a friendly call-to-action paragraph with a bold internal link to '[**{domain}{permalink}**](https://{domain}{permalink})' using the article title as anchor text.\n\n"
        f"{language_specific_instructions}"
        f"{related_links_text}"
        f"CONTENT REQUIREMENTS:\n"
        f"1. Make each section extremely detailed, professional, and comprehensive - cover the topic '{subject}' with expert-level depth and analysis.\n"
        f"2. Include real-world examples, case studies, statistics, and actionable step-by-step instructions with specific details and metrics when possible.\n"
        f"3. Write in a professional, authoritative {language} tone that establishes genuine expertise. Address readers directly using 'you' and 'your' to increase engagement.\n"
        f"4. Add 6-8 external links to highly authoritative sources (major publications, university studies, industry leaders) with descriptive anchor text.\n"
        f"5. Maintain a keyword density of 2-3% for the main keyword '{subject}'. Aim for the main keyword to appear approximately 1-2 times per 100 words. This creates optimal density without keyword stuffing.\n"
        f"6. Heavily optimize for LSI (Latent Semantic Indexing) keywords by incorporating 10-15 semantically related terms to '{subject}' throughout the article. These should appear naturally within the content.\n"
        f"7. Create advanced internal linking: Convert 7-8 appropriate LSI keywords or phrases into internal links pointing to: [**{domain}/keyword-phrase**](https://{domain}/keyword-phrase) - replace spaces with hyphens in the URL portion.\n"
        f"8. For related articles provided, include links to them using descriptive anchor text that naturally fits within the content, with at least one link in each major section.\n"
        f"9. DO NOT include table of contents - start directly with the first major H2 section after the introduction and infographic.\n"
        f"10. Include multiple professional-quality formatted elements: 2-3 bulleted lists, 2-3 numbered lists, and at least one detailed comparison table or data table formatted with markdown.\n"
        f"11. Make each H2, H3, and H4 heading compelling, specific, and keyword-optimized. Follow SEO best practices: include numbers in some headings, use 'how to,' 'why,' or question formats in others, and keep headings under 60 characters.\n"
        f"12. For each heading section, start with a concise topic sentence that summarizes the section, followed by a detailed, data-backed explanation (250-400 words per H2 section).\n"
        f"13. Develop a clear hierarchy: Each H2 should have 2-3 H3 subsections, and at least one H3 should contain 1-2 H4 subsections for even more detailed analysis.\n"
        f"14. DO NOT include FAQ sections - directly incorporate questions and their detailed answers into the relevant sections as regular paragraphs and headings.\n"
        f"15. When mentioning specific tools, resources, or techniques, provide expert insights about their implementation, advantages, limitations, and competitive alternatives.\n"
    )
    
    try:
        # Get the Gemini client
        client = get_gemini_client()
        
        # Generate article via API request
        response = client.generate_content(article_prompt, model, max_output_tokens=8192)
        
        if not response:
            raise Exception("Failed to generate article content")
        
        return response
            
    except Exception as e:
        print(f"\nError generating article: {str(e)}")
        raise e

def replace_image_placeholders(article: str, subject: str) -> str:
    """Replace image placeholders with actual images"""
    
    # Find all image placeholders
    pattern = r'\[IMAGE: (.*?)\]'
    image_descriptions = re.findall(pattern, article)
    
    if not image_descriptions:
        # If no placeholders found, return the original article
        return article
    
    # Replace each placeholder with an image
    modified_article = article
    for i, description in enumerate(image_descriptions):
        try:
            # The query should be specific and include the subject and the description
            query = f"{subject} {description}"
            
            # Use our combined image search function
            images = get_images(query)
            
            # Try up to 3 times with different queries if needed
            attempts = 0
            while not images and attempts < 3:
                attempts += 1
                if attempts == 1:
                    # Try just the description
                    query = description
                elif attempts == 2:
                    # Try the subject
                    query = subject
                else:
                    # Try a more generic term related to the subject
                    query = f"{subject} image"
                
                print(f"Retry {attempts} for image search with query: '{query}'")
                images = get_images(query)
            
            if images and len(images) > 0:
                # Select an image (first one for reliability)
                image = images[0]  # Use first image for consistency
                img_url = image['url']
                img_title = f"{description}"
                img_source = image.get('source', 'Image Search')
                
                # Verify image is valid and accessible
                if is_valid_image_url(img_url):
                    # Create markdown image tag
                    img_tag = f"![{img_title}]({img_url})"
                    
                    # Replace the placeholder with the image tag
                    modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                    print(f"Successfully added image for '{description}' from {img_source}")
                else:
                    # Try next image in the results if first one is invalid
                    found_valid = False
                    for alt_img in images[1:]:
                        alt_url = alt_img['url']
                        if is_valid_image_url(alt_url):
                            img_tag = f"![{img_title}]({alt_url})"
                            modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                            print(f"Using alternative valid image for '{description}' from {alt_img.get('source', 'Image Search')}")
                            found_valid = True
                            break
                    
                    # If no valid images found, try a different query
                    if not found_valid:
                        # Try different, more reliable queries
                        backup_queries = [
                            f"{subject} {description} tutorial image",
                            f"{subject} {description} high quality",
                            "professional blogging image",  # Generic backup
                            "content marketing illustration" # Ultimate fallback
                        ]
                        
                        for backup_query in backup_queries:
                            backup_images = get_images(backup_query)
                            if backup_images and len(backup_images) > 0:
                                for backup_img in backup_images:
                                    if is_valid_image_url(backup_img['url']):
                                        img_tag = f"![{img_title}]({backup_img['url']})"
                                        modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                                        print(f"Using backup image for '{description}' with query '{backup_query}'")
                                        found_valid = True
                                        break
                            if found_valid:
                                break
                        
                        # If still no valid images, use a stock image from a reliable source
                        if not found_valid:
                            # Define reliable stock images that are guaranteed to work
                            reliable_stock_images = [
                                "https://cdn.pixabay.com/photo/2015/09/03/08/10/blog-920730_1280.jpg",
                                "https://cdn.pixabay.com/photo/2015/01/08/18/24/programming-593312_1280.jpg",
                                "https://cdn.pixabay.com/photo/2014/05/02/21/49/blogger-336371_1280.jpg",
                                "https://cdn.pixabay.com/photo/2015/07/17/22/43/student-849825_1280.jpg",
                                "https://cdn.pixabay.com/photo/2015/01/20/13/13/ipad-605439_1280.jpg"
                            ]
                            
                            # Use a reliable stock image based on image number to vary them
                            stock_index = i % len(reliable_stock_images)
                            reliable_url = reliable_stock_images[stock_index]
                            img_tag = f"![{img_title}]({reliable_url})"
                            modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                            print(f"Using reliable stock image for '{description}' after exhausting all options")
            else:
                # If all attempts failed, use a stock image instead of leaving blank
                print(f"Failed to find any images for '{description}' after multiple attempts")
                
                # Define reliable stock images that are guaranteed to work
                reliable_stock_images = [
                    "https://cdn.pixabay.com/photo/2015/09/03/08/10/blog-920730_1280.jpg",
                    "https://cdn.pixabay.com/photo/2015/01/08/18/24/programming-593312_1280.jpg",
                    "https://cdn.pixabay.com/photo/2014/05/02/21/49/blogger-336371_1280.jpg",
                    "https://cdn.pixabay.com/photo/2015/07/17/22/43/student-849825_1280.jpg",
                    "https://cdn.pixabay.com/photo/2015/01/20/13/13/ipad-605439_1280.jpg"
                ]
                
                # Use a reliable stock image based on image number to vary them
                stock_index = i % len(reliable_stock_images)
                reliable_url = reliable_stock_images[stock_index]
                img_tag = f"![{img_title}]({reliable_url})"
                modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                print(f"Using reliable stock image for '{description}' as fallback")
        
        except Exception as e:
            print(f"Error replacing image placeholder '{description}': {str(e)}")
            # Mark the error in a comment
            modified_article = modified_article.replace(
                f"[IMAGE: {description}]", 
                f"<!-- Error finding image: {description} - {str(e)} -->"
            )
    
    return modified_article

def generate_frontmatter(title: str, subject: str, permalink: str, category: Optional[str] = None, 
                        article_content: Optional[str] = None) -> str:
    """Generate Jekyll frontmatter for the article"""
    
    from modules.seo_utils import generate_tags_from_title, extract_featured_image
    
    today = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Generate tags from title and subject
    tags = generate_tags_from_title(title, subject)
    
    # Use provided category or generate from subject if none provided
    if not category:
        main_category = subject.split()[0] if subject.split() else subject
    else:
        main_category = category
    
    # Extract featured image if article content is provided
    featured_image = None
    if article_content:
        featured_image = extract_featured_image(article_content)
    
    # Create frontmatter content as string
    content = "---\n"
    
    # Ensure title is properly quoted for YAML if it contains special characters
    if ":" in title or "'" in title or '"' in title or "[" in title or "]" in title or "{" in title or "}" in title:
        # Use YAML literal block scalar for complex titles
        content += "title: |\n"
        content += f"  {title}\n"
    else:
        # For simple titles, add single quotes
        content += f"title: '{title}'\n"
    
    content += f"date: {today}\n"
    content += f"author: Cart labs\n"
    
    # Ensure layout is set to a valid Jekyll layout
    content += f"layout: post\n"
    
    # Add featured image if found
    if featured_image:
        print(f"Adding featured image to frontmatter: {featured_image}")
        # Ensure image URL is properly formatted
        featured_image = featured_image.replace("'", "").replace('"', "")
        content += f"image: '{featured_image}'\n"  # Use single quotes to prevent YAML issues
    
    content += "tag:\n"
    for tag in tags:  # Using tags generated from title and subject
        # Ensure tags are properly formatted
        safe_tag = tag.replace("'", "").replace('"', "").strip()
        if safe_tag:
            content += f"  - {safe_tag}\n"
    
    # Ensure permalink is valid
    safe_permalink = permalink.replace("'", "").replace('"', "").strip()
    content += f"permalink: '{safe_permalink}'\n"
    
    content += "categories:\n"
    # Ensure category is valid
    safe_category = main_category.replace("'", "").replace('"', "").strip()
    content += f"  - {safe_category}\n"
    
    content += "---\n\n"
    
    return content

def generate_seo_article(subject: str, domain: str = "cartlab.web.id", 
                        model_title: str = "gemini-1.5-flash", 
                        model_article: str = "gemini-1.5-flash", 
                        category: Optional[str] = None) -> Dict[str, Any]:
    """Generate a complete SEO article with images and frontmatter"""
    
    try:
        # Detect language from subject
        language = detect_language(subject)
        
        # Generate title
        title = generate_title(subject, language, model_title)
        
        # Generate permalink
        permalink = f"/{slugify(title)}"
        
        # Find related articles
        related_articles = article_links_manager.get_related_articles(subject, permalink)
        
        # Generate article content with related links
        article = generate_article(title, subject, domain, permalink, language, model_article, related_articles)
        
        # Replace image placeholders with real images
        article_with_images = replace_image_placeholders(article, subject)
        
        # Add <!--more--> tag after the first paragraph
        paragraphs = article_with_images.split('\n\n')
        if paragraphs:
            paragraphs[0] += '\n\n<!--more-->\n\n'
            article_with_images = '\n\n'.join(paragraphs)
        
        # Generate Jekyll frontmatter with optional custom category and extract featured image
        frontmatter = generate_frontmatter(title, subject, permalink, category, article_with_images)
        
        # Create full markdown document with frontmatter
        markdown_content = frontmatter + article_with_images
        
        # Add the article to our link manager for future reference
        article_links_manager.add_article(title, subject, permalink)
        
        return {
            "title": title,
            "article": article_with_images,
            "markdown": markdown_content,
            "permalink": permalink,
            "subject": subject,
            "category": category
        }
        
    except Exception as e:
        return {"error": str(e)}

def batch_generate_articles(domain: str = "cartlab.web.id", output_folder: str = "_posts", 
                          default_category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate multiple articles from a list of subjects"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Read subjects from file
    subjects = []
    if os.path.exists("keyword.txt"):
        with open("keyword.txt", "r", encoding="utf-8") as file:
            subjects = [line.strip() for line in file if line.strip()]
    
    if not subjects:
        return []
    
    # Initialize list to track generated articles
    generated_articles = []
    errors = []
    
    # Process each subject
    for idx, subject in enumerate(subjects):
        try:
            print(f"Generating article for: {subject}")
            
            # Generate SEO article with appropriate category
            result = generate_seo_article(subject, domain, "gemini-1.5-flash", "gemini-2.0-flash", default_category)
            
            if "error" in result:
                print(f"Error generating article: {result['error']}")
                errors.append(f"{subject}: {result['error']}")
                continue

            title = result["title"]
            markdown_content = result["markdown"]
            
            # Create date prefix for Jekyll post
            date_prefix = datetime.now().strftime('%Y-%m-%d-')
            
            # File paths for markdown post in Jekyll format
            file_md = os.path.join(output_folder, f"{date_prefix}{slugify(title)}.md")

            # Save markdown file with frontmatter
            with open(file_md, "w", encoding="utf-8") as md_file:
                md_file.write(markdown_content)

            # Add to generated articles list
            article_data = {
                "subject": subject,
                "title": title,
                "file": file_md,
                "permalink": result["permalink"],
                "category": default_category if default_category else subject.split()[0] if subject.split() else subject
            }
            
            generated_articles.append(article_data)
            
            print(f"Generated: {title}")
            print(f"Saved to: {file_md}")
            
            # Small delay to avoid hitting API rate limits
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            errors.append(f"{subject}: {str(e)}")
    
    # Return the generated articles list
    return generated_articles