import os
import json
import shutil
import zipfile
import markdown
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

# HTML export function
def export_to_html(articles: List[Dict[str, Any]]) -> str:
    """
    Export articles to HTML files
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Path to the zip file containing the exported HTML
    """
    # Create export directory
    export_dir = "exports/html"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Process each article
    for article in articles:
        try:
            # Get article details
            title = article.get("title", "Untitled")
            file_path = article.get("file", "")
            
            if not file_path or not os.path.exists(file_path):
                print(f"Skipping article '{title}' - file not found: {file_path}")
                continue
            
            # Read the markdown content
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'codehilite']
            )
            
            # Create HTML document
            html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
            
            # Create safe filename
            safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
            safe_title = safe_title.replace(" ", "_")
            html_file_name = f"{safe_title}.html"
            
            # Write HTML file
            with open(os.path.join(export_dir, html_file_name), "w", encoding="utf-8") as f:
                f.write(html_doc)
            
            print(f"Exported HTML for '{title}'")
        
        except Exception as e:
            print(f"Error exporting HTML for article '{article.get('title', 'Unknown')}': {str(e)}")
    
    # Create a zip file of all HTML files
    zip_path = "exports/html_export.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(export_dir):
            if file.endswith(".html"):
                zipf.write(os.path.join(export_dir, file), file)
    
    print(f"HTML export completed. Zip file created at: {zip_path}")
    return zip_path

# WordPress XML export function
def export_to_wordpress(articles: List[Dict[str, Any]]) -> str:
    """
    Export articles to WordPress XML format
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Path to the WordPress XML file
    """
    # Create export directory if it doesn't exist
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Create WordPress XML structure
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:excerpt", "http://wordpress.org/export/1.2/excerpt/")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:wfw", "http://wellformedweb.org/CommentAPI/")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    rss.set("xmlns:wp", "http://wordpress.org/export/1.2/")
    
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "SEO Blog"
    ET.SubElement(channel, "link").text = "https://cartlab.web.id"
    ET.SubElement(channel, "description").text = "SEO Articles"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(channel, "language").text = "en-US"
    ET.SubElement(channel, "wp:wxr_version").text = "1.2"
    ET.SubElement(channel, "wp:base_site_url").text = "https://cartlab.web.id"
    ET.SubElement(channel, "wp:base_blog_url").text = "https://cartlab.web.id"
    
    # Process each article
    for article in articles:
        try:
            # Get article details
            title = article.get("title", "Untitled")
            file_path = article.get("file", "")
            
            if not file_path or not os.path.exists(file_path):
                print(f"Skipping article '{title}' - file not found: {file_path}")
                continue
            
            # Read the markdown content
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'codehilite']
            )
            
            # Create item in XML
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = title
            ET.SubElement(item, "link").text = f"https://cartlab.web.id{article.get('permalink', '')}"
            ET.SubElement(item, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, "dc:creator").text = "Cart Labs"
            
            # Add categories
            category = article.get("category", "")
            if category:
                cat_elem = ET.SubElement(item, "category")
                cat_elem.set("domain", "category")
                cat_elem.set("nicename", category.lower().replace(" ", "-"))
                cat_elem.text = category
            
            # Add content
            content_elem = ET.SubElement(item, "content:encoded")
            content_elem.text = ET.CDATA(html_content)
            
            # Add WordPress specific elements
            ET.SubElement(item, "wp:post_id").text = str(hash(title) % 100000000)
            ET.SubElement(item, "wp:post_date").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ET.SubElement(item, "wp:post_date_gmt").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ET.SubElement(item, "wp:post_name").text = article.get("permalink", "").strip("/")
            ET.SubElement(item, "wp:status").text = "publish"
            ET.SubElement(item, "wp:post_type").text = "post"
            
            print(f"Added WordPress XML for '{title}'")
        
        except Exception as e:
            print(f"Error exporting WordPress XML for article '{article.get('title', 'Unknown')}': {str(e)}")
    
    # Create the XML file
    xml_path = os.path.join(export_dir, "wordpress_export.xml")
    tree = ET.ElementTree(rss)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    
    print(f"WordPress XML export completed. File created at: {xml_path}")
    return xml_path

# Blogspot XML export function
def export_to_blogspot(articles: List[Dict[str, Any]]) -> str:
    """
    Export articles to Blogspot XML format
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Path to the Blogspot XML file
    """
    # Create export directory if it doesn't exist
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Create Blogspot XML structure
    rss = ET.Element("feed")
    rss.set("xmlns", "http://www.w3.org/2005/Atom")
    rss.set("xmlns:blogger", "http://schemas.google.com/blogger/2008")
    rss.set("xmlns:georss", "http://www.georss.org/georss")
    rss.set("xmlns:gd", "http://schemas.google.com/g/2005")
    rss.set("xmlns:thr", "http://purl.org/syndication/thread/1.0")
    
    ET.SubElement(rss, "title").text = "SEO Blog"
    ET.SubElement(rss, "subtitle").text = "SEO Articles"
    link = ET.SubElement(rss, "link")
    link.set("href", "https://cartlab.web.id")
    link.set("rel", "self")
    
    # Process each article
    for article in articles:
        try:
            # Get article details
            title = article.get("title", "Untitled")
            file_path = article.get("file", "")
            
            if not file_path or not os.path.exists(file_path):
                print(f"Skipping article '{title}' - file not found: {file_path}")
                continue
            
            # Read the markdown content
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'codehilite']
            )
            
            # Create entry in XML
            entry = ET.SubElement(rss, "entry")
            ET.SubElement(entry, "id").text = f"tag:blogger.com,1999:blog-123.post-{hash(title) % 100000000}"
            ET.SubElement(entry, "title").text = title
            
            published = ET.SubElement(entry, "published")
            published.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            updated = ET.SubElement(entry, "updated")
            updated.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Add categories/labels
            category = article.get("category", "")
            if category:
                cat_elem = ET.SubElement(entry, "category")
                cat_elem.set("scheme", "http://www.blogger.com/atom/ns#")
                cat_elem.set("term", category)
            
            # Add content
            content_elem = ET.SubElement(entry, "content")
            content_elem.set("type", "html")
            content_elem.text = html_content
            
            # Author info
            author = ET.SubElement(entry, "author")
            ET.SubElement(author, "name").text = "Cart Labs"
            ET.SubElement(author, "email").text = "admin@cartlab.web.id"
            
            print(f"Added Blogspot XML for '{title}'")
        
        except Exception as e:
            print(f"Error exporting Blogspot XML for article '{article.get('title', 'Unknown')}': {str(e)}")
    
    # Create the XML file
    xml_path = os.path.join(export_dir, "blogspot_export.xml")
    tree = ET.ElementTree(rss)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    
    print(f"Blogspot XML export completed. File created at: {xml_path}")
    return xml_path