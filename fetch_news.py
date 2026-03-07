import requests
import feedparser
from datetime import datetime
import pytz
import re
import hashlib
from deep_translator import GoogleTranslator

# הגדרת מקורות החדשות עם תתי-נושאים
RSS_FEEDS = {
    'חדשות ישראל': {
        'חדשות ופוליטיקה': [
            {'name': 'Ynet', 'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml'},
            {'name': 'מעריב', 'url': 'https://www.maariv.co.il/Rss/RssFeedsMivzakim'}
        ],
        'כלכלה והייטק מקומי': [
            {'name': 'כלכליסט', 'url': 'https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml'},
            {'name': 'Geektime', 'url': 'https://www.geektime.co.il/feed/'}
        ]
    },
    'AI וטכנולוגיה': {
        'בינה מלאכותית (AI)': [
            {'name': 'AI News', 'url': 'https://www.artificialintelligence-news.com/feed/'},
            {'name': 'MIT Tech Review', 'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed'}
        ],
        'טכנולוגיה עולמית': [
            {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml'},
            {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'}
        ]
    }
}

def clean_html(raw_html):
    """מנקה תגיות HTML ומשאיר טקסט קריא וארוך יותר"""
    if not raw_html: return "אין תקציר זמין לידיעה זו."
    clean_text = re.sub('<[^<]+?>', '', raw_html).strip()
    clean_text = clean_text.replace('"', '&quot;').replace("'", "&#39;")
    return clean_text[:300] + '...' if len(clean_text) > 300 else clean_text

def smart_translate(text, is_hebrew_source):
    """תרגום חכם שבודק מה שפת המקור ומתרגם בהתאם"""
    if not text or len(text.strip()) < 2: return text
    try:
        if is_hebrew_source:
            # מקור בעברית -> נתרגם לאנגלית
            return GoogleTranslator(source='iw', target='en').translate(text)
        else:
            # מקור באנגלית -> נתרגם לעברית
            return GoogleTranslator(source='en', target='iw').translate(text)
    except:
        return text

def fetch_news():
    categorized_news = {cat: {} for cat in RSS_FEEDS.keys()}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for main_cat, sub_cats in RSS_FEEDS.items():
        for sub_cat, feeds in sub_cats.items():
            categorized_news[main_cat][sub_cat] = []
            for feed in feeds:
                try:
                    response = requests.get(feed['url'], headers=headers, timeout=15)
                    if response.status_code == 200:
                        feed_data = feedparser.parse(response.content)
                        # לוקח עד 6 ידיעות מכל מקור כדי לשמור על גיוון ולא להעמיס
                        for entry in feed_data.entries[:6]:
                            sort_time = entry.published_parsed if hasattr(entry, 'published_parsed') else None
                            article_id = "article_" + hashlib.md5(entry.link.encode()).hexdigest()[:8]
                            
                            title_clean = entry.title
                            summary_clean = clean_html(entry.get('summary', entry.get('description', '')))
                            
                            # בדיקה פשוטה: האם הכותרת מכילה אותיות בעברית?
                            is_hebrew = any("\u0590" <= c <= "\u05EA" for c in title_clean)
                            
                            if is_hebrew:
                                title_he = title_clean
                                summary_he = summary_clean
                                title_en = smart_translate(title_clean, True)
                                summary_en = smart_translate(summary_clean, True)
                            else:
                                title_en = title_clean
                                summary_en = summary_clean
                                title_he = smart_translate(title_clean, False)
                                summary_he = smart_translate(summary_clean, False)

                            categorized_news[main_cat][sub_cat].append({
                                'id': article_id,
                                'source': feed['name'],
                                'title_he': title_he,
                                'title_en': title_en,
                                'summary_he': summary_he,
                                'summary_en': summary_en,
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
            if not items: continue # דילוג אם אין ידיעות
            sub_cat_en = smart_translate(sub_cat, True)
            content_html += f'<div class="sub-header"><span class="lang-he">{sub_cat}</span><span class="lang-en" style="display:none;">{sub_cat_en}</span></div>\n<div class="news-grid">\n'
            
            for i in items:
                # התקציר מופיע עכשיו בגוף הכרטיס ולא בטולטיפ
                content_html += f"""
                <div class="card" id="{i['id']}">
                    <div class="card-content">
                        <a href="{i['link']}" target="_blank" class="article-title">
                            <span class="lang-he">{i['title_he']}</span>
                            <span class="lang-en" style="display:none;">{i['title_en']}</span>
                        </a>
                        <p class="article-summary">
                            <span class="lang-he">{i['summary_he']}</span>
                            <span class="lang-en" style="display:none;">{i['summary_en']}</span>
                        </p>
                    </div>
                    
                    <div class="card-footer">
                        <div class="meta">
                            <span class="source-tag">{i['source']}</span>
                            <span class="time-tag">{i['published']}</span>
                        </div>
                        <div class="actions">
                            <button class="action-btn share-btn" onclick="shareLink('{i['id']}')" title="שתף קישור">
                                <i class="fas fa-share-alt"></i>
                            </button>
                            <a href="{i['link']}" target="_blank" class="action-btn link-btn" title="לכתבה המקורית">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                        </div>
                    </div>
                </div>\n"""
            content_html += '</div>\n'
        content_html += '</div>\n'

    html_top = """<!DOCTYPE html>
<html lang="he" dir="rtl" id="html-tag">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מדברים בינה - הבית של חובבי ה-AI בישראל</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700;900&display=swap');
        
        :root { 
            --bg: #f3f4f6; --card: rgba(255, 255, 255, 0.9); --text: #1f2937; 
            --accent: #4f46e5; --accent-hover: #4338ca; --dim: #6b7280; 
            --border: rgba(0,0,0,0.05); --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        [data-theme="dark"] { 
            --bg: #111827; --card: rgba(31, 41, 55, 0.9); --text: #f9fafb; 
            --accent: #6366f1; --accent-hover: #818cf8; --dim: #9ca3af; 
            --border: rgba(255,255,255,0.05); --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        
        body { 
            font-family: 'Heebo', sans-serif; background: var(--bg); color: var(--text); 
            margin: 0; transition: background 0.3s, color 0.3s; padding-bottom: 60px; scroll-behavior: smooth;
        }
        
        .nav-bar { 
            display: flex; justify-content: space-between; align-items: center; padding: 15px 30px; 
            background: var(--card); backdrop-filter: blur(10px); box-shadow: var(--shadow); 
            position: sticky; top: 0; z-index: 1000; border-bottom: 1px solid var(--border);
        }
        
        .controls { display: flex; gap: 12px; }
        .btn { 
            background: transparent; border: 2px solid var(--dim); color: var(--text); 
            padding: 8px 16px; border-radius: 20px; cursor: pointer; font-weight: bold; 
            transition: all 0.2s ease; font-family: 'Heebo', sans-serif;
        }
        .btn:hover { border-color: var(--accent); color: var(--accent); transform: translateY(-2px); }
        
        .hero { 
            text-align: center; padding: 60px 20px; 
            background: linear-gradient(135deg, var(--accent), #3b82f6); color: white;
            box-shadow: inset 0 -10px 20px rgba(0,0,0,0.1);
        }
        .hero h1 { font-size: 2.8rem; font-weight: 900; margin: 0; letter-spacing: -0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        
        .tabs { display: flex; justify-content: center; gap: 15px; margin: -25px auto 30px; padding: 0 10px; flex-wrap: wrap; position: relative; z-index: 10; }
        .tab-btn { 
            padding: 12px 30px; border: none; background: var(--card); color: var(--text); 
            border-radius: 30px; cursor: pointer; font-weight: bold; font-size: 1.1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border); font-family: 'Heebo', sans-serif;
        }
        .tab-btn:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
        .tab-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
        
        .container { max-width: 1400px; margin: auto; padding: 0 20px; }
        
        .sub-header { 
            font-size: 1.8rem; font-weight: 800; margin: 40px 0 20px; 
            color: var(--text); display: flex; align-items: center; gap: 10px;
        }
        .sub-header::before { content: ''; display: block; width: 6px; height: 24px; background: var(--accent); border-radius: 4px; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; }
        
        .card { 
            background: var(--card); backdrop-filter: blur(10px); padding: 25px; 
            border-radius: 16px; border: 1px solid var(--border); box-shadow: var(--shadow); 
            transition: all 0.3s ease; display: flex; flex-direction: column; justify-content: space-between; 
        }
        .card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); border-color: var(--accent); }
        
        .article-title { color: var(--text); text-decoration: none; font-weight: 800; font-size: 1.3rem; display: block; margin-bottom: 10px; line-height: 1.3; transition: color 0.2s; }
        .article-title:hover { color: var(--accent); }
        
        .article-summary { color: var(--dim); font-size: 1rem; line-height: 1.6; margin-bottom: 20px; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
        
        .card-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid var(--border); }
        .meta { display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem; color: var(--dim); font-weight: bold; }
        .source-tag { background: rgba(99, 102, 241, 0.1); color: var(--accent); padding: 4px 10px; border-radius: 6px; display: inline-block; width: fit-content; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .actions { display: flex; gap: 10px; }
        .action-btn { 
            background: var(--bg); border: none; color: var(--dim); width: 40px; height: 40px; 
            border-radius: 10px; display: flex; align-items: center; justify-content: center; 
            cursor: pointer; transition: 0.2s; text-decoration: none; font-size: 1.1rem;
        }
        .action-btn:hover { background: var(--accent); color: white; transform: scale(1.05); }
        
        .highlight-card { animation: pulse 2s infinite; border-color: var(--accent); }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); } 70% { box-shadow: 0 0 0 15px rgba(99, 102, 241, 0); } 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); } }
        
        [dir="ltr"] { text-align: left; } [dir="rtl"] { text-align: right; }
    </style>
</head>
<body data-theme="dark">
    <div class="nav-bar">
        <div class="controls">
            <button class="btn" onclick="toggleTheme()" title="החלף עיצוב"><i class="fas fa-moon"></i></button>
            <button class="btn" onclick="toggleLang()" id="lang-btn">EN / עב</button>
        </div>
        <div id="update-time" style="font-size: 0.9rem; color: var(--dim); font-weight: bold;">
            <span class="lang-he">עודכן:</span><span class="lang-en" style="display:none;">Updated:</span> """

    html_mid1 = """
        </div>
    </div>
    <div class="hero">
        <h1 id="main-title">
            <i class="fas fa-robot"></i> 
            <span class="lang-he">מדברים בינה - הבית של חובבי ה-AI בישראל</span>
            <span class="lang-en" style="display:none;">Talking AI - The Home of AI Enthusiasts</span>
        </h1>
    </div>
    <div class="tabs">
"""
    
    html_mid2 = """    </div>
    <div class="container" id="content-area">
"""
    
    html_bottom = """    </div>
    
    <div id="toast" style="visibility: hidden; min-width: 250px; background: var(--accent); color: white; text-align: center; border-radius: 30px; padding: 12px 24px; position: fixed; z-index: 2000; left: 50%; bottom: 30px; transform: translateX(-50%); font-weight: bold; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
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
            
            html.setAttribute('dir', isHeb ? 'ltr' : 'rtl');
            html.setAttribute('lang', isHeb ? 'en' : 'he');
            
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
            const url = window.location.href.split('#')[0] + '#' + articleId;
            navigator.clipboard.writeText(url).then(() => {
                const toast = document.getElementById("toast");
                toast.innerHTML = document.getElementById('html-tag').getAttribute('lang') === 'en' ? "Link copied!" : "הקישור הועתק!";
                toast.style.visibility = "visible";
                setTimeout(() => { toast.style.visibility = "hidden"; }, 3000);
            });
        }
        
        document.querySelector('.tab-btn').click();
        if(localStorage.getItem('theme') === 'light') toggleTheme();
        if(localStorage.getItem('lang') === 'en') toggleLang();
        
        window.onload = () => {
            const hash = window.location.hash;
            if (hash) {
                const targetCard = document.querySelector(hash);
                if (targetCard) {
                    const parentSection = targetCard.closest('.news-section');
                    if(parentSection) {
                        const tabBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.textContent.trim() === parentSection.id);
                        if(tabBtn) tabBtn.click();
                    }
                    targetCard.classList.add('highlight-card');
                    setTimeout(() => targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' }), 500);
                    setTimeout(() => targetCard.classList.remove('highlight-card'), 6000);
                }
            }
        };
    </script>
</body>
</html>"""

    final_html = html_top + update_time + html_mid1 + tabs_html + html_mid2 + content_html + html_bottom
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_html)

if __name__ == '__main__':
    news = fetch_news()
    update_dashboard(news)
