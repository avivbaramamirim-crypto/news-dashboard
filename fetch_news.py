import requests
import feedparser
from datetime import datetime
import pytz
import re
import hashlib
from deep_translator import GoogleTranslator

# הגדרת מקורות החדשות עם תתי-נושאים
RSS_FEEDS = {
    'ישראל': {
        'חדשות ופוליטיקה': [{'name': 'Google News Israel', 'url': 'https://news.google.com/rss/search?q=israel&hl=he&gl=IL&ceid=IL:he'}],
        'מבזקים שוטפים': [{'name': 'ynet', 'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml'}]
    },
    'AI וטכנולוגיה': {
        'בינה מלאכותית': [{'name': 'AI News', 'url': 'https://www.artificialintelligence-news.com/feed/'}],
        'הייטק ופיתוח': [{'name': 'Hacker News', 'url': 'https://news.ycombinator.com/rss'}]
    }
}

def clean_html(raw_html):
    """מנקה תגיות HTML מהתקציר עבור הטולטיפ"""
    if not raw_html: return "אין תקציר זמין לידיעה זו."
    clean_text = re.sub('<[^<]+?>', '', raw_html).strip()
    clean_text = clean_text.replace('"', '&quot;').replace("'", "&#39;")
    return clean_text[:200] + '...' if len(clean_text) > 200 else clean_text

def translate_safe(text, target='en'):
    """מתרגם טקסט בבטחה, אם נכשל מחזיר מקור"""
    if not text: return ""
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return text

def fetch_news():
    categorized_news = {cat: {} for cat in RSS_FEEDS.keys()}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for main_cat, sub_cats in RSS_FEEDS.items():
        for sub_cat, feeds in sub_cats.items():
            categorized_news[main_cat][sub_cat] = []
            for feed in feeds:
                try:
                    response = requests.get(feed['url'], headers=headers, timeout=10)
                    if response.status_code == 200:
                        feed_data = feedparser.parse(response.content)
                        # לוקח ידיעות ומוסיף להן שדה מיון לפי זמן
                        for entry in feed_data.entries[:10]:
                            sort_time = entry.published_parsed if hasattr(entry, 'published_parsed') else None
                            
                            # יצירת מזהה ייחודי עבור הלינק לשיתוף
                            article_id = "article_" + hashlib.md5(entry.link.encode()).hexdigest()[:8]
                            
                            # שליפת תקציר לטולטיפ
                            summary_he = clean_html(entry.get('summary', entry.get('description', '')))
                            title_he = entry.title
                            
                            categorized_news[main_cat][sub_cat].append({
                                'id': article_id,
                                'source': feed['name'],
                                'title_he': title_he,
                                'title_en': translate_safe(title_he),
                                'summary_he': summary_he,
                                'summary_en': translate_safe(summary_he),
                                'link': entry.link,
                                'published': entry.get('published', '')[:16],
                                'sort_time': sort_time
                            })
                except Exception as e:
                    print(f"Error fetching {feed['name']}: {e}")
                    
            # מיון הידיעות בכל תת-קטגוריה מהחדש לישן
            categorized_news[main_cat][sub_cat].sort(
                key=lambda x: x['sort_time'] if x['sort_time'] else (0,), reverse=True
            )
            
    return categorized_news

def update_dashboard(news_data):
    filename = 'index.html'
    tz = pytz.timezone('Asia/Jerusalem')
    update_time = datetime.now(tz).strftime('%d/%m/%Y %H:%M')

    tabs_html = ""
    for cat in news_data.keys():
        tabs_html += f'<button class="tab-btn" onclick="showCategory(\'{cat}\')">{cat}</button>\n'

    content_html = ""
    for main_cat, sub_cats in news_data.items():
        content_html += f'<div id="{main_cat}" class="news-section" style="display:none">\n'
        
        for sub_cat, items in sub_cats.items():
            sub_cat_en = translate_safe(sub_cat)
            content_html += f'<div class="sub-header"><span class="lang-he">{sub_cat}</span><span class="lang-en" style="display:none;">{sub_cat_en}</span></div>\n<div class="news-grid">\n'
            
            for i in items:
                content_html += f"""
                <div class="card" id="{i['id']}">
                    <div class="tooltip">
                        <a href="{i['link']}" target="_blank" class="article-title">
                            <span class="lang-he">{i['title_he']}</span>
                            <span class="lang-en" style="display:none;">{i['title_en']}</span>
                        </a>
                        <span class="tooltiptext">
                            <strong class="lang-he">תקציר:</strong><strong class="lang-en" style="display:none;">Summary:</strong><br>
                            <span class="lang-he">{i['summary_he']}</span>
                            <span class="lang-en" style="display:none;">{i['summary_en']}</span>
                        </span>
                    </div>
                    
                    <div class="card-footer">
                        <div class="meta">
                            <span class="source-tag">{i['source']}</span>
                            <span class="time-tag">{i['published']}</span>
                        </div>
                        <div class="actions">
                            <button class="action-btn share-btn" onclick="shareLink('{i['id']}')" title="שתף קישור לאתר שלי">
                                <i class="fas fa-share-alt"></i>
                            </button>
                            <a href="{i['link']}" target="_blank" class="action-btn link-btn" title="לכתבה המקורית">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                        </div>
                    </div>
                </div>\n"""
            content_html += '</div>\n' # סגירת news-grid
        content_html += '</div>\n' # סגירת news-section

    html_top = """<!DOCTYPE html>
<html lang="he" dir="rtl" id="html-tag">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>לוח החדשות של אוהד ברעם</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --text: #1e293b; --accent: #2563eb; --dim: #64748b; --border: rgba(0,0,0,0.05); }
        [data-theme="dark"] { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #38bdf8; --dim: #94a3b8; --border: rgba(255,255,255,0.05); }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: var(--text); margin: 0; transition: 0.3s; padding-bottom: 50px; scroll-behavior: smooth; }
        .nav-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--card); box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000; }
        .controls { display: flex; gap: 10px; }
        .btn { background: var(--bg); border: 1px solid var(--dim); color: var(--text); padding: 8px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        .hero { text-align: center; padding: 40px 20px; background: linear-gradient(135deg, var(--accent), #1d4ed8); color: white; }
        .tabs { display: flex; justify-content: center; gap: 10px; margin: 20px 0; padding: 0 10px; flex-wrap: wrap; }
        .tab-btn { padding: 10px 25px; border: none; background: var(--card); color: var(--text); border-radius: 25px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .tab-btn.active { background: var(--accent); color: white; transform: scale(1.05); }
        .container { max-width: 1200px; margin: auto; padding: 0 15px; }
        
        .sub-header { font-size: 1.5rem; font-weight: bold; margin: 30px 0 15px; border-bottom: 2px solid var(--accent); padding-bottom: 5px; color: var(--accent); }
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        
        .card { background: var(--card); padding: 20px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; justify-content: space-between; position: relative; }
        .card:hover { transform: translateY(-3px); border-color: var(--accent); }
        .article-title { color: var(--text); text-decoration: none; font-weight: bold; font-size: 1.15rem; display: block; margin-bottom: 15px; line-height: 1.4; }
        
        /* Tooltip CSS */
        .tooltip { position: relative; display: block; }
        .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: var(--card); color: var(--text); border: 1px solid var(--accent); text-align: right; border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 110%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.3s; box-shadow: 0 10px 25px rgba(0,0,0,0.2); font-size: 0.9rem; font-weight: normal; line-height: 1.5; pointer-events: none; }
        .tooltip .tooltiptext::after { content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: var(--accent) transparent transparent transparent; }
        [dir="ltr"] .tooltip .tooltiptext { text-align: left; }
        .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; pointer-events: auto; }
        
        .card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border); }
        .meta { display: flex; flex-direction: column; gap: 5px; font-size: 0.8rem; color: var(--dim); }
        .source-tag { background: rgba(37, 99, 235, 0.1); color: var(--accent); padding: 4px 8px; border-radius: 4px; font-weight: bold; display: inline-block; width: fit-content; }
        
        .actions { display: flex; gap: 8px; }
        .action-btn { background: var(--bg); border: 1px solid var(--border); color: var(--text); width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; text-decoration: none; font-size: 1rem; }
        .action-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }
        
        /* Highlight specific article if linked */
        .highlight-card { animation: pulse 2s infinite; border-color: var(--accent); }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(37, 99, 235, 0); } 100% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); } }
        
        [dir="ltr"] { text-align: left; } [dir="rtl"] { text-align: right; }
    </style>
</head>
<body data-theme="dark">
    <div class="nav-bar">
        <div class="controls">
            <button class="btn" onclick="toggleTheme()" title="החלף עיצוב"><i class="fas fa-moon"></i></button>
            <button class="btn" onclick="toggleLang()" id="lang-btn">EN / עב</button>
        </div>
        <div id="update-time" style="font-size: 0.85rem; color: var(--dim); font-weight: bold;">
            <span class="lang-he">עודכן:</span><span class="lang-en" style="display:none;">Updated:</span> {update_time}
        </div>
    </div>
    <div class="hero">
        <h1 id="main-title">
            <i class="fas fa-globe"></i> 
            <span class="lang-he">לוח החדשות של אוהד ברעם</span>
            <span class="lang-en" style="display:none;">Ohad Baram's News Dashboard</span>
        </h1>
    </div>
    <div class="tabs">
"""
    
    html_mid = """    </div>
    <div class="container" id="content-area">
"""
    
    html_bottom = """    </div>
    
    <div id="toast" style="visibility: hidden; min-width: 250px; background-color: var(--accent); color: #fff; text-align: center; border-radius: 8px; padding: 16px; position: fixed; z-index: 2000; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 1rem;">
        הקישור הועתק!
    </div>

    <script>
        function toggleTheme() {
            const body = document.body;
            const isDark = body.getAttribute('data-theme') === 'dark';
            body.setAttribute('data-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        }
        
        function toggleLang() {
            const html = document.getElementById('html-tag');
            const isHeb = html.getAttribute('dir') === 'rtl';
            
            // Switch HTML attributes
            html.setAttribute('dir', isHeb ? 'ltr' : 'rtl');
            html.setAttribute('lang', isHeb ? 'en' : 'he');
            
            // Toggle all language spans
            document.querySelectorAll('.lang-he').forEach(el => el.style.display = isHeb ? 'none' : 'inline-block');
            document.querySelectorAll('.lang-en').forEach(el => el.style.display = isHeb ? 'inline-block' : 'none');
            
            localStorage.setItem('lang', isHeb ? 'en' : 'he');
        }
        
        function showCategory(id) {
            document.querySelectorAll('.news-section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).style.display = 'block';
            event.currentTarget.classList.add('active');
        }
        
        function shareLink(articleId) {
            // מעתיק את הקישור הישיר לידיעה באתר שלך
            const url = window.location.href.split('#')[0] + '#' + articleId;
            navigator.clipboard.writeText(url).then(() => {
                const toast = document.getElementById("toast");
                toast.innerHTML = document.getElementById('html-tag').getAttribute('lang') === 'en' ? "Link copied!" : "הקישור הועתק!";
                toast.style.visibility = "visible";
                setTimeout(() => { toast.style.visibility = "hidden"; }, 3000);
            });
        }
        
        // Setup on load
        document.querySelector('.tab-btn').click();
        if(localStorage.getItem('theme') === 'light') toggleTheme();
        if(localStorage.getItem('lang') === 'en') toggleLang();
        
        // Check if arrived from a shared link and scroll to it
        window.onload = () => {
            const hash = window.location.hash;
            if (hash) {
                const targetCard = document.querySelector(hash);
                if (targetCard) {
                    // Find which tab it belongs to and open it
                    const parentSection = targetCard.closest('.news-section');
                    if(parentSection) {
                        const tabBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.textContent.trim() === parentSection.id);
                        if(tabBtn) tabBtn.click();
                    }
                    // Highlight and scroll
                    targetCard.classList.add('highlight-card');
                    setTimeout(() => targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' }), 500);
                    setTimeout(() => targetCard.classList.remove('highlight-card'), 6000);
                }
            }
        };
    </script>
</body>
</html>"""

    final_html = html_top + tabs_html + html_mid + content_html + html_bottom
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_html)

if __name__ == '__main__':
    news = fetch_news()
    update_dashboard(news)
