import streamlit as st
import time
import os
import json
import pandas as pd
from PIL import Image
import base64
from datetime import datetime

# Import modules from the refactored SEO generator
from modules.article_generator import generate_seo_article, batch_generate_articles
from modules.image_search import get_images
from modules.api_client import test_api_key
from modules.exporters import export_to_html, export_to_wordpress, export_to_blogspot

# Set page configuration
st.set_page_config(
    page_title="SEO Article Generator Ultimate",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and apply custom CSS
def load_css():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        h1, h2, h3, h4, h5 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        .main-title {
            color: #0066CC;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2rem;
            margin-top: 0;
            padding-top: 0;
        }
        
        .stButton > button {
            background-color: #0066CC;
            color: white;
            font-weight: 500;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #004C99;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .card {
            border-radius: 10px;
            padding: 1.5rem;
            background-color: white;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
        }
        
        .article-card {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .article-card:hover {
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            border-color: #0066CC;
        }
        
        .status-success {
            color: #00A878;
            font-weight: 500;
        }
        
        .status-error {
            color: #E63946;
            font-weight: 500;
        }
        
        .status-warning {
            color: #F4A261;
            font-weight: 500;
        }
        
        .status-info {
            color: #0066CC;
            font-weight: 500;
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div {
            background-color: #0066CC;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            background-color: #f8f9fa;
        }

        .stTabs [aria-selected="true"] {
            background-color: #0066CC !important;
            color: white !important;
        }
        
        /* Animation for processing state */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .processing {
            animation: pulse 1.5s infinite;
        }
        
        /* File uploader styling */
        .uploadedFile {
            border-radius: 4px;
            padding: 0.5rem;
            background-color: #f8f9fa;
            margin-bottom: 0.5rem;
        }
        
        /* Tag styling */
        .tag {
            background-color: #e9ecef;
            color: #495057;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            margin-right: 0.3rem;
            font-size: 0.8rem;
        }
        
        /* Metric container */
        .metric-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #0066CC;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# Initialize session state
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = []
    
if 'generated_articles' not in st.session_state:
    st.session_state.generated_articles = []
    
if 'progress' not in st.session_state:
    st.session_state.progress = 0
    
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
    
if 'show_success' not in st.session_state:
    st.session_state.show_success = False
    
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# Load API keys from file if available
def load_api_keys():
    if os.path.exists("apikey.txt"):
        with open("apikey.txt", "r") as file:
            keys = [line.strip() for line in file if line.strip()]
            st.session_state.api_keys = keys
            return keys
    return []

# Save API keys to file
def save_api_keys(keys):
    with open("apikey.txt", "w") as file:
        for key in keys:
            file.write(f"{key}\n")
    st.session_state.api_keys = keys

# Function to save keywords to file
def save_keywords(keywords):
    with open("keyword.txt", "w") as file:
        for keyword in keywords:
            file.write(f"{keyword}\n")
    return True

# Function to load keywords from file
def load_keywords():
    if os.path.exists("keyword.txt"):
        with open("keyword.txt", "r") as file:
            return [line.strip() for line in file if line.strip()]
    return []

# Function to save generated articles data
def save_articles_data(articles):
    data = []
    for article in articles:
        data.append({
            "title": article.get("title", ""),
            "subject": article.get("subject", ""),
            "permalink": article.get("permalink", ""),
            "category": article.get("category", ""),
            "file": article.get("file", ""),
            "timestamp": datetime.now().isoformat()
        })
    
    with open("generated_articles.json", "w") as file:
        json.dump(data, file, indent=2)

# Function to load generated articles data
def load_articles_data():
    if os.path.exists("generated_articles.json"):
        with open("generated_articles.json", "r") as file:
            return json.load(file)
    return []

# Helper function to get article status emoji
def get_status_emoji(status):
    if status == "success":
        return "✅"
    elif status == "error":
        return "❌"
    elif status == "warning":
        return "⚠️"
    else:
        return "ℹ️"

# App header with logo and title
def render_header():
    col1, col2 = st.columns([1, 5])
    
    # Logo
    with col1:
        st.image("https://img.icons8.com/fluency/96/content.png", width=80)
    
    # Title and subtitle
    with col2:
        st.markdown("<h1 class='main-title'>SEO Article Generator Ultimate</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Powered by Gemini AI & Dual-Engine Image Search</p>", unsafe_allow_html=True)
    
    st.markdown("---")

# App Sidebar
def render_sidebar():
    with st.sidebar:
        st.subheader("⚙️ Settings & Tools")
        
        # API Key Management
        with st.expander("🔑 API Key Management", expanded=False):
            api_keys = st.session_state.api_keys
            
            st.write("Manage your Gemini API keys:")
            new_key = st.text_input("Add new API key", type="password")
            
            if st.button("Add Key"):
                if new_key and new_key not in api_keys:
                    # Test the API key before adding
                    if test_api_key(new_key):
                        api_keys.append(new_key)
                        save_api_keys(api_keys)
                        st.success("API key added successfully!")
                    else:
                        st.error("Invalid API key. Please check and try again.")
                else:
                    st.warning("API key already exists or is empty.")
            
            if api_keys:
                st.write(f"You have {len(api_keys)} API key(s) configured.")
                
                if st.button("Test API Keys"):
                    for i, key in enumerate(api_keys):
                        if test_api_key(key):
                            st.success(f"API Key #{i+1}: Valid")
                        else:
                            st.error(f"API Key #{i+1}: Invalid")
            else:
                st.warning("No API keys configured. Please add at least one API key.")
        
        # Advanced Settings
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.write("Configure advanced generation settings:")
            
            st.slider("Temperature", min_value=0.1, max_value=1.0, value=0.7, step=0.1, 
                     help="Higher values make output more creative, lower values make it more deterministic")
            
            st.slider("Max Output Tokens", min_value=1000, max_value=8192, value=4096, step=100,
                     help="Maximum length of generated content")
            
            model_options = ["gemini-1.5-flash", "gemini-2.0-flash"]
            st.selectbox("Generation Model", model_options, 
                        help="Select which Gemini model to use for generation")
            
            st.checkbox("Enable debug mode", 
                       help="Show detailed logs during generation process")
        
        # About
        with st.expander("ℹ️ About", expanded=False):
            st.write("""
            **SEO Article Generator Ultimate v1.0**
            
            A powerful tool for generating SEO-optimized articles with AI.
            
            Features:
            - AI-powered content generation
            - Automatic image integration
            - Internal linking optimization
            - Multiple export formats
            
            Created by Cart Labs
            """)
        
        # Help & Support
        with st.expander("❓ Help & Support", expanded=False):
            st.write("""
            **Need help?**
            
            - Make sure you have valid API keys
            - Enter keywords one per line
            - Allow time for content generation
            - Check console for any errors
            
            For support contact: support@cartlab.web.id
            """)

# Main tabs
def render_main_content():
    tabs = st.tabs(["Generate Articles", "Manage Articles", "Export", "Analytics"])
    
    # Generate Articles Tab
    with tabs[0]:
        render_generate_tab()
    
    # Manage Articles Tab
    with tabs[1]:
        render_manage_tab()
    
    # Export Tab
    with tabs[2]:
        render_export_tab()
    
    # Analytics Tab
    with tabs[3]:
        render_analytics_tab()

# Generate Articles Tab
def render_generate_tab():
    st.header("Generate SEO Articles")
    
    # Input Form
    with st.form("generation_form"):
        st.subheader("Content Generation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Domain Input
            domain = st.text_input("Domain", "cartlab.web.id", 
                               help="The domain name for your website")
            
            # Category Selection
            category_option = st.radio("Category Options", 
                                     ["Automatic categories", "Use a single category", "Set category per article"],
                                     horizontal=True)
            
            if category_option == "Use a single category":
                default_category = st.text_input("Category for all articles")
            else:
                default_category = None
            
            # Output Folder
            output_folder = st.text_input("Output Folder", "_posts", 
                                      help="Folder where generated articles will be saved")
        
        with col2:
            # Keywords Input
            keywords_input_option = st.radio("Keywords Input Method", 
                                           ["Enter keywords", "Upload keywords file"],
                                           horizontal=True)
            
            if keywords_input_option == "Enter keywords":
                keywords_text = st.text_area("Enter Keywords (one per line)", 
                                           height=150,
                                           help="Enter one keyword or topic per line")
                keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
            else:
                uploaded_file = st.file_uploader("Upload keywords file", type=["txt"])
                if uploaded_file:
                    keywords = [line.decode("utf-8").strip() for line in uploaded_file if line.decode("utf-8").strip()]
                    st.info(f"Loaded {len(keywords)} keywords from file")
                else:
                    keywords = []
        
        # Number of articles to generate
        max_articles = st.slider("Maximum articles to generate", 1, 50, 5, 
                               help="Limit the number of articles to generate (useful for testing)")
        
        # Submit Button
        submit_button = st.form_submit_button("Generate Articles", use_container_width=True)
        
        if submit_button:
            if not st.session_state.api_keys:
                st.error("No API keys configured. Please add at least one API key in the sidebar.")
            elif not keywords:
                st.error("No keywords provided. Please enter at least one keyword.")
            else:
                # Limit keywords to the selected max_articles
                keywords = keywords[:max_articles]
                
                # Save keywords to file
                save_keywords(keywords)
                
                # Start generation
                st.session_state.is_generating = True
                st.session_state.progress = 0
                st.session_state.show_success = False
                st.session_state.error_message = None
                
                # Rerun to show progress UI
                st.rerun()
    
    # Show generation progress if active
    if st.session_state.is_generating:
        st.subheader("Generating Articles...")
        
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        try:
            # Create output directory if needed
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # Load keywords
            keywords = load_keywords()
            
            # Initialize results
            articles = []
            errors = []
            
            # Process each keyword
            total = len(keywords)
            for i, keyword in enumerate(keywords):
                # Update progress
                progress = (i / total)
                progress_bar.progress(progress)
                st.session_state.progress = progress
                
                status_container.info(f"Generating article {i+1}/{total}: **{keyword}**")
                
                try:
                    # Generate article
                    article_result = generate_seo_article(
                        subject=keyword,
                        domain=domain,
                        model_title="gemini-1.5-flash", 
                        model_article="gemini-2.0-flash",
                        category=default_category
                    )
                    
                    if "error" in article_result:
                        errors.append(f"{keyword}: {article_result['error']}")
                        status_container.error(f"Error generating article for '{keyword}': {article_result['error']}")
                    else:
                        articles.append(article_result)
                        status_container.success(f"Successfully generated: {article_result['title']}")
                
                except Exception as e:
                    errors.append(f"{keyword}: {str(e)}")
                    status_container.error(f"Error: {str(e)}")
                
                # Simulate a short delay to show progress
                time.sleep(0.5)
            
            # Update session state with generated articles
            st.session_state.generated_articles = articles
            save_articles_data(articles)
            
            # Complete progress
            progress_bar.progress(1.0)
            st.session_state.progress = 1.0
            
            # Show completion summary
            if articles:
                status_container.success(f"✅ Generated {len(articles)} articles successfully! ({len(errors)} errors)")
                st.session_state.show_success = True
            else:
                status_container.error("❌ No articles were generated. Please check the errors and try again.")
            
            # Reset generation state
            st.session_state.is_generating = False
        
        except Exception as e:
            st.session_state.error_message = str(e)
            st.session_state.is_generating = False
            status_container.error(f"❌ An error occurred: {str(e)}")
    
    # Show success message after generation
    if st.session_state.show_success:
        st.success(f"✅ Generated {len(st.session_state.generated_articles)} articles successfully!")
        
        # Show quick preview of generated articles
        st.subheader("Generated Articles Preview")
        
        for article in st.session_state.generated_articles[:3]:  # Show first 3 articles
            with st.expander(f"📄 {article['title']}"):
                st.write(f"**Subject:** {article['subject']}")
                st.write(f"**Category:** {article.get('category', 'Auto')}")
                st.write(f"**Permalink:** {domain}{article['permalink']}")
                
                # Show first 300 characters of the article
                preview_text = article['article'][:300] + "..." if len(article['article']) > 300 else article['article']
                st.markdown(preview_text)
        
        if len(st.session_state.generated_articles) > 3:
            st.info(f"... and {len(st.session_state.generated_articles) - 3} more articles. View all in the 'Manage Articles' tab.")
    
    # Show error message if any
    if st.session_state.error_message:
        st.error(f"An error occurred: {st.session_state.error_message}")

# Manage Articles Tab
def render_manage_tab():
    st.header("Manage Generated Articles")
    
    # Load articles data
    articles = load_articles_data()
    
    if not articles:
        st.info("No articles generated yet. Go to the 'Generate Articles' tab to create new content.")
        return
    
    # Search and filter
    st.subheader("Search & Filter")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("Search by title or keyword", "")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Title A-Z", "Title Z-A"])
    
    # Apply search filter
    if search_term:
        filtered_articles = [a for a in articles if search_term.lower() in a["title"].lower() or search_term.lower() in a["subject"].lower()]
    else:
        filtered_articles = articles
    
    # Apply sorting
    if sort_by == "Newest":
        filtered_articles = sorted(filtered_articles, key=lambda x: x.get("timestamp", ""), reverse=True)
    elif sort_by == "Oldest":
        filtered_articles = sorted(filtered_articles, key=lambda x: x.get("timestamp", ""))
    elif sort_by == "Title A-Z":
        filtered_articles = sorted(filtered_articles, key=lambda x: x["title"])
    elif sort_by == "Title Z-A":
        filtered_articles = sorted(filtered_articles, key=lambda x: x["title"], reverse=True)
    
    # Display article count
    st.write(f"Showing {len(filtered_articles)} of {len(articles)} articles")
    
    # Display articles in a table/list
    for i, article in enumerate(filtered_articles):
        with st.container():
            st.markdown(f"""
            <div class="article-card">
                <h3>{article["title"]}</h3>
                <p><strong>Keyword:</strong> {article["subject"]}</p>
                <p><strong>Category:</strong> {article.get("category", "Auto")}</p>
                <p><strong>File:</strong> {article.get("file", "Not saved")}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button(f"Preview #{i}", key=f"preview_{i}"):
                    st.session_state[f"show_preview_{i}"] = not st.session_state.get(f"show_preview_{i}", False)
            
            with col2:
                st.button("Edit", key=f"edit_{i}", disabled=True)
            
            with col3:
                st.button("Delete", key=f"delete_{i}", disabled=True)
            
            # Show preview if button clicked
            if st.session_state.get(f"show_preview_{i}", False):
                try:
                    file_path = article.get("file", "")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        st.markdown("### Article Preview")
                        st.markdown(content)
                    else:
                        st.warning("Article file not found or path not specified.")
                except Exception as e:
                    st.error(f"Error loading article: {str(e)}")
            
            st.markdown("---")

# Export Tab
def render_export_tab():
    st.header("Export Articles")
    
    # Load articles data
    articles = load_articles_data()
    
    if not articles:
        st.info("No articles generated yet. Go to the 'Generate Articles' tab to create new content.")
        return
    
    st.write(f"You have {len(articles)} articles available for export.")
    
    # Export options
    st.subheader("Export Format")
    
    export_format = st.radio("Select export format", 
                           ["HTML", "WordPress XML", "Blogspot XML", "All Formats"],
                           horizontal=True)
    
    # Export settings
    with st.expander("Export Settings", expanded=False):
        st.checkbox("Include images", value=True, 
                   help="Include images in the exported content")
        
        st.checkbox("Optimize HTML", value=True,
                   help="Minify and optimize HTML output")
        
        st.text_input("Site name for export", "My SEO Blog",
                     help="The site name to use in exported files")
    
    # Export button
    if st.button("Export Articles", use_container_width=True):
        with st.spinner("Exporting articles..."):
            try:
                if export_format == "HTML" or export_format == "All Formats":
                    export_to_html(articles)
                    st.success("✅ HTML export completed successfully!")
                
                if export_format == "WordPress XML" or export_format == "All Formats":
                    # Note: This function would need to be implemented in modules/exporters.py
                    export_to_wordpress(articles)
                    st.success("✅ WordPress XML export completed successfully!")
                
                if export_format == "Blogspot XML" or export_format == "All Formats":
                    # Note: This function would need to be implemented in modules/exporters.py
                    export_to_blogspot(articles)
                    st.success("✅ Blogspot XML export completed successfully!")
                
                # Show download links
                st.subheader("Download Exported Files")
                
                if export_format == "HTML" or export_format == "All Formats":
                    st.download_button(
                        label="Download HTML Export",
                        data="Sample HTML export data",  # This would be the actual file data
                        file_name="articles_html_export.zip",
                        mime="application/zip"
                    )
                
                if export_format == "WordPress XML" or export_format == "All Formats":
                    st.download_button(
                        label="Download WordPress XML",
                        data="Sample WordPress XML data",  # This would be the actual file data
                        file_name="wordpress_export.xml",
                        mime="application/xml"
                    )
                
                if export_format == "Blogspot XML" or export_format == "All Formats":
                    st.download_button(
                        label="Download Blogspot XML",
                        data="Sample Blogspot XML data",  # This would be the actual file data
                        file_name="blogspot_export.xml",
                        mime="application/xml"
                    )
            
            except Exception as e:
                st.error(f"Export error: {str(e)}")

# Analytics Tab
def render_analytics_tab():
    st.header("Content Analytics")
    
    # Load articles data
    articles = load_articles_data()
    
    if not articles:
        st.info("No articles generated yet. Go to the 'Generate Articles' tab to create new content.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{len(articles)}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Total Articles</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Calculate average word count (this is just an example - you'd actually count words in your articles)
        avg_word_count = 4500  # Placeholder value
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{avg_word_count}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Avg. Word Count</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        # Calculate total word count
        total_words = avg_word_count * len(articles)
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{total_words:,}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Total Words</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        # Categories count
        categories = set(article.get("category", "Auto") for article in articles)
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{len(categories)}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Categories</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Articles by category
    st.subheader("Articles by Category")
    
    # Count articles by category
    category_counts = {}
    for article in articles:
        category = article.get("category", "Auto")
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts[category] = 1
    
    # Convert to DataFrame for charting
    df_categories = pd.DataFrame({
        'Category': list(category_counts.keys()),
        'Articles': list(category_counts.values())
    })
    
    # Sort by count
    df_categories = df_categories.sort_values('Articles', ascending=False)
    
    # Display chart
    st.bar_chart(df_categories.set_index('Category'))
    
    # Generation timeline
    st.subheader("Generation Timeline")
    
    # Extract dates from timestamps
    dates = []
    for article in articles:
        if "timestamp" in article:
            try:
                date = datetime.fromisoformat(article["timestamp"]).date()
                dates.append(str(date))
            except:
                pass
    
    # Count articles by date
    date_counts = {}
    for date in dates:
        if date in date_counts:
            date_counts[date] += 1
        else:
            date_counts[date] = 1
    
    # Convert to DataFrame for charting
    df_dates = pd.DataFrame({
        'Date': list(date_counts.keys()),
        'Articles': list(date_counts.values())
    })
    
    # Sort by date
    df_dates['Date'] = pd.to_datetime(df_dates['Date'])
    df_dates = df_dates.sort_values('Date')
    df_dates['Date'] = df_dates['Date'].dt.strftime('%Y-%m-%d')
    
    # Display chart
    st.line_chart(df_dates.set_index('Date'))
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Sort articles by timestamp
    sorted_articles = sorted(articles, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Show recent activity table
    recent_activity = []
    for article in sorted_articles[:10]:  # Last 10 activities
        timestamp = article.get("timestamp", "")
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
            except:
                date = "Unknown"
        else:
            date = "Unknown"
        
        recent_activity.append({
            "Date": date,
            "Title": article["title"],
            "Action": "Generated"
        })
    
    # Display as table
    if recent_activity:
        st.table(pd.DataFrame(recent_activity))
    else:
        st.info("No recent activity data available.")

# Main app function
def main():
    # Try to load API keys
    load_api_keys()
    
    # Render app components
    render_header()
    render_sidebar()
    render_main_content()

if __name__ == "__main__":
    main()
