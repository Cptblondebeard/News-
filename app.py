import streamlit as st
import feedparser
import cloudscraper
from bs4 import BeautifulSoup
import trafilatura
import google.generativeai as genai
import re
import html
import concurrent.futures

st.set_page_config(page_title="AI Briefing", layout="centered", initial_sidebar_state="collapsed")

# --- Hardcoded API Key ---
GEMINI_API_KEY = "AQ.Ab8RN6JlC3lfsmWmva2j3iFsheXQWNNw7_1rl-ot2sVADEmD4g"

# --- Premium OLED Mobile CSS ---
st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.stApp { background-color: #000000; }

.block-container {
    padding-top: 0rem;
    padding-bottom: 1rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    max-width: 600px;
}

/* Elegant Edge-to-Edge Single Card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
    border: none;
    background: #111111;
    padding: 24px;
    margin-bottom: 10px;
    box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.5);
    min-height: 60vh;
    display: flex;
    flex-direction: column;
}

h3 {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    line-height: 1.4 !important;
    color: #FFFFFF !important;
    margin-top: 15px !important;
    margin-bottom: 20px !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.badge-container {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}
.meta-badge {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #FF3366;
}
.date-badge {
    font-size: 0.8rem;
    color: #888888;
}

.ai-summary {
    font-size: 1.15rem;
    line-height: 1.65;
    color: #E2E8F0;
    padding: 20px;
    background-color: #1A1A1A;
    border-left: 3px solid #FF3366;
    border-radius: 6px;
    margin-top: 5px;
    margin-bottom: 15px;
}

.app-header {
    text-align: center;
    color: #FFFFFF;
    font-size: 2rem;
    font-weight: 800;
    padding-top: 10px;
    padding-bottom: 15px;
}
.app-header span { color: #FF3366; }

.nav-counter {
    text-align: center; 
    color: #666; 
    font-weight: 700; 
    font-size: 1rem;
    padding-top: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='app-header'>News<span>.AI</span></div>", unsafe_allow_html=True)

# --- Perfectly Segregated RSS Feeds ---
FEEDS = {
    "Tamil": {
        "Top Stories": {
            "Hindu Tamil": "https://www.hindutamil.in/rss/tamilnadu",
            "BBC Tamil": "https://feeds.bbci.co.uk/tamil/rss.xml",
            "OneIndia Tamil": "https://tamil.oneindia.com/rss/tamil-news-fb.xml",
            "Samayam Tamil": "https://tamil.samayam.com/rssfeeds/47355132.cms",
            "News18 Tamil": "https://tamil.news18.com/rss/tamil-nadu.xml",
            "Zee Tamil": "https://zeenews.india.com/tamil/rss/tamil-nadu-news.xml"
        },
        "World": {
            "Hindu Tamil": "https://www.hindutamil.in/rss/world",
            "BBC Tamil": "https://feeds.bbci.co.uk/tamil/global/rss.xml",
            "OneIndia Tamil": "https://tamil.oneindia.com/rss/international-fb.xml",
            "Samayam Tamil": "https://tamil.samayam.com/rssfeeds/47355152.cms",
            "News18 Tamil": "https://tamil.news18.com/rss/world.xml",
            "Zee Tamil": "https://zeenews.india.com/tamil/rss/world-news.xml"
        },
        "Business": {
            "Hindu Tamil": "https://www.hindutamil.in/rss/business",
            "OneIndia Tamil": "https://tamil.goodreturns.in/rss/money-fb.xml",
            "Samayam Tamil": "https://tamil.samayam.com/rssfeeds/47337920.cms",
            "News18 Tamil": "https://tamil.news18.com/rss/business.xml",
            "Zee Tamil": "https://zeenews.india.com/tamil/rss/business.xml"
        },
        "Sports": {
            "Hindu Tamil": "https://www.hindutamil.in/rss/sports",
            "OneIndia Tamil": "https://tamil.oneindia.com/rss/sports-fb.xml",
            "Samayam Tamil": "https://tamil.samayam.com/rssfeeds/47337905.cms",
            "News18 Tamil": "https://tamil.news18.com/rss/sports.xml",
            "Zee Tamil": "https://zeenews.india.com/tamil/rss/sports.xml"
        },
        "Entertainment": {
            "Hindu Tamil": "https://www.hindutamil.in/rss/cinema",
            "OneIndia Tamil": "https://tamil.oneindia.com/rss/movies-fb.xml",
            "Samayam Tamil": "https://tamil.samayam.com/rssfeeds/47337890.cms",
            "News18 Tamil": "https://tamil.news18.com/rss/entertainment.xml",
            "Zee Tamil": "https://zeenews.india.com/tamil/rss/cinema.xml"
        }
    },
    "English": {
        "Top Stories": {
            "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
            "Indian Express": "https://indianexpress.com/section/india/feed/",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/top-news/rssfeed.xml",
            "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
        },
        "World": {
            "The Hindu": "https://www.thehindu.com/news/international/feeder/default.rss",
            "Indian Express": "https://indianexpress.com/section/world/feed/",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
            "NDTV": "https://feeds.feedburner.com/ndtvnews-world-news",
        },
        "Business": {
            "The Hindu": "https://www.thehindu.com/business/feeder/default.rss",
            "Indian Express": "https://indianexpress.com/section/business/feed/",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml",
            "NDTV": "https://feeds.feedburner.com/ndtvprofit-latest",
        },
        "Sports": {
            "The Hindu": "https://www.thehindu.com/sport/feeder/default.rss",
            "Indian Express": "https://indianexpress.com/section/sports/feed/",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/sports/rssfeed.xml",
            "NDTV": "https://feeds.feedburner.com/ndtvsports-latest",
        },
        "Entertainment": {
            "The Hindu": "https://www.thehindu.com/entertainment/feeder/default.rss",
            "Indian Express": "https://indianexpress.com/section/entertainment/feed/",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/entertainment/rssfeed.xml",
            "NDTV": "https://feeds.feedburner.com/ndtvmovies-latest",
        }
    }
}

# --- Navigation Filters ---
with st.expander("⚙️ Filter Feed Options"):
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("🌐 Language", options=["Tamil", "English"])
    with col2:
        categories = list(FEEDS[language].keys())
        selected_category = st.selectbox("📂 Category", options=categories)

    col3, col4 = st.columns([7, 3])
    with col3:
        available_sources = list(FEEDS[language][selected_category].keys())
        selected_source = st.selectbox("🗞️ Source", options=["All Sources"] + available_sources)
    with col4:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

# --- Session State Management ---
current_filters = (language, selected_category, selected_source)
if 'last_filters' not in st.session_state or st.session_state.last_filters != current_filters:
    st.session_state.current_index = 0
    st.session_state.last_filters = current_filters

def clean_html_text(text):
    if not text: return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", text)).strip()

@st.cache_data(ttl=900)
def fetch_rss_articles(language, category, source_filter):
    all_items = []
    feed_dict = FEEDS[language][category]
    sources_to_fetch = feed_dict.items() if source_filter == "All Sources" else [(source_filter, feed_dict[source_filter])]
    
    scraper = cloudscraper.create_scraper()
    for source_name, url in sources_to_fetch:
        try:
            response = scraper.get(url, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                for entry in feed.entries[:15]:
                    title = clean_html_text(entry.get('title', 'No Title'))
                    link = entry.get('link', '#')
                    date = entry.get('published', 'Recent')
                    if link.startswith('http'):
                        all_items.append({"source": source_name, "title": title, "link": link, "date": date[:16]})
        except Exception:
            continue
    return all_items

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_and_summarize(url, lang):
    """Downloads and summarizes a single article. Cached indefinitely so returning users load instantly."""
    try:
        # Extract
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        response = scraper.get(url, timeout=12, allow_redirects=True)
        if response.status_code != 200: return "Publisher connection blocked."
            
        extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False)
        text = extracted if (extracted and len(extracted) > 150) else None
        
        if not text:
            soup = BeautifulSoup(response.text, "html.parser")
            for junk in soup(["script", "style", "nav", "header", "footer", "aside"]): junk.decompose()
            blocks = [p.get_text(separator=" ", strip=True) for p in soup.find_all(["p", "div", "span"]) if len(p.get_text(strip=True)) > 65]
            text = " ".join(blocks)
            
        if not text or len(text) < 150:
            return "Publisher blocked extraction or content was too short to summarize."

        # Summarize
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-3.5-flash-lite')
        prompt = f"""
        You are an elite news editor formatting content for a mobile app. 
        Read the text and provide a highly concise, objective summary in exactly 60 words or less. 
        Do not use introductory phrases. Just provide the raw news facts.
        Write the summary in {lang}.
        Text: {text[:8000]} 
        """
        return model.generate_content(prompt).text
    except Exception as e:
        return "AI Summary temporarily unavailable."

# --- Main Render Pipeline ---
all_articles = fetch_rss_articles(language, selected_category, selected_source)

if all_articles:
    if st.session_state.current_index >= len(all_articles):
        st.session_state.current_index = 0
        
    article = all_articles[st.session_state.current_index]
    
    # --- Background Concurrency Window (Pre-fetching +5 cards) ---
    start_idx = st.session_state.current_index
    end_idx = min(start_idx + 5, len(all_articles))
    prefetch_urls = [a['link'] for a in all_articles[start_idx:end_idx]]
    
    summaries = {}
    with st.spinner("Synthesizing AI Briefings..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(fetch_and_summarize, url, language): url for url in prefetch_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                summaries[url] = future.result()

    current_summary = summaries.get(article['link'], "Summary currently unavailable.")
    
    # --- UI Render ---
    with st.container(border=True):
        st.markdown(f"<div class='badge-container'><span class='meta-badge'>{article['source']}</span><span class='date-badge'>{article['date']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"### {article['title']}")
        
        # True Inshorts Layout: Summary is displayed directly without needing a button press
        st.markdown(f"<div class='ai-summary'>{current_summary}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='margin-top: auto; text-align: right; padding-top: 25px;'><a href='{article['link']}' target='_blank' style='color: #888888; text-decoration: none; font-size: 0.85rem;'>Read original article ↗</a></div>", unsafe_allow_html=True)
    
    # Navigation Dock
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("◀ Prev", disabled=(st.session_state.current_index == 0), use_container_width=True):
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        st.markdown(f"<div class='nav-counter'>{st.session_state.current_index + 1} / {len(all_articles)}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("Next ▶", disabled=(st.session_state.current_index == len(all_articles) - 1), use_container_width=True):
            st.session_state.current_index += 1
            st.rerun()
else:
    st.info(f"No {selected_category.lower()} articles could be fetched right now.")