import requests
import feedparser
from datetime import datetime
import pytz

# הגדרת מקורות החדשות
RSS_FEEDS = {
    'ישראל': [
        {'name': 'Google News Israel', 'url': 'https://news.google.com/rss/search?q=israel&hl=he&gl=IL&ceid=IL:he'},
        {'name': 'ynet', 'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml'}
    ],
    'AI וטכנולוגיה': [
        {'name': 'AI News', 'url': 'https://www.artificialintelligence-news.com/feed/'},
        {'name': 'Hacker News', 'url': 'https://news.ycombinator.com/rss'}
    ]
}

def fetch_news():
    categorized_news = {cat: [] for cat in RSS_FEEDS.keys()}
    headers = {'User-Agent': 'Mozilla/5.0'}
    for category, feeds in RSS_FEEDS.items():
        for feed in feeds:
            try:
                response = requests.get(feed['url'], headers=headers, timeout=10)
                if response.status_code == 200:
                    feed_data = feedparser.parse(response.content)
                    for entry in feed_data.entries[:10]:
                        categorized_news[category].append({
                            'source': feed['name'],
                            'title': entry.title,
                            'link': entry.link,
                            'published': entry.get('published', '')
                        })
            except Exception as e:
                print(f"Error fetching {feed['name']}: {e}")
    return categorized_news

def update_dashboard(news_data):
    # כאן נמצא התיקון הקריטי: יצירת קובץ index.html במקום השם הישן
    filename = 'index.html' 
    
    # הגדרת שעון ישראל
    tz = pytz.timezone('Asia/Jerusalem')
    update_time = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl" id="html-tag">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>לוח החדשות של אוהד ברעם</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {{
                --bg: #f8fafc; --card: #ffffff; --text: #1e293b; --accent: #2563eb; --dim: #64748b;
            }}
            [data-theme="dark"] {{
                --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #38bdf8; --dim: #94a3b8;
            }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: var(--text); margin: 0; transition: background 0.3s, color 0.3s; padding-bottom: 50px; }}
            .nav-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--card); box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000; }}
            .controls {{ display: flex; gap: 10px; }}
            .btn {{ background: var(--bg); border: 1px solid var(--dim); color: var(--text); padding: 8px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.2s; }}
            .btn:hover {{ border-color: var(--accent); color: var(--accent); }}
            
            .hero {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, var(--accent), #1d4ed8); color: white; }}
            .hero h1 {{ margin: 0; font-size: 2.2rem; }}
            .weather-widget {{ margin-top: 15px; font-size: 1.1rem; background: rgba(255,255,255,0.1); display: inline-block; padding: 10px 20px; border-radius: 50px; backdrop-filter: blur(5px); }}
            
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; padding: 0 10px; flex-wrap: wrap; }}
            .tab-btn {{ padding: 10px 25px; border: none; background: var(--card); color: var(--text); border-radius: 25px; cursor: pointer; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s; }}
            .tab-btn.active {{ background: var(--accent); color: white; transform: translateY(-2px); }}

            .container {{ max-width: 1100px; margin: auto; padding: 0 15px; }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: var(--card); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; justify-content: space-between; }}
            .card:hover {{ transform: translateY(-5px); border-color: var(--accent); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
            .card a {{ color: var(--text); text-decoration: none; font-weight: bold; font-size: 1.1rem; display: block; margin-bottom: 15px; line-height: 1.4; }}
            .card .meta {{ font-size: 0.8rem; color: var(--dim); display: flex; justify-content: space-between; align-items: center; }}
            .card .source-tag {{ background: rgba(37, 99, 235, 0.1); color: var(--accent); padding: 4px 8px; border-radius: 4px; font-weight: bold; }}

            [dir="ltr"] {{ text-align: left; }}
            [dir="rtl"] {{ text-align: right; }}
        </style>
    </head>
    <body data-theme="dark">
        <div class="nav-bar">
            <div class="controls">
                <button class="btn" onclick="toggleTheme()" title="החלף עיצוב"><i class="fas fa-moon"></i></button>
                <button class="btn" onclick="toggleLang()">EN / עב</button>
            </div>
            <div id="update-time" style="font-size: 0.85rem; color: var(--dim); font-weight: bold;">עודכן: {update_time}</div>
        </div>

        <div class="hero">
            <h1 id="main-title"><i class="fas fa-globe"></i> לוח החדשות של אוהד ברעם</h1>
            <div class="weather-widget" id="weather">ישראל: 22°C | בהיר <i class="fas fa-sun"></i></div>
        </div>

        <div class="tabs">
            {" ".join([f'<button class="tab-btn" onclick="showCategory(\'{cat}\')">{cat}</button>' for cat in news_data.keys()])}
        </div>

        <div class="container" id="content-area">
            { "".join([f'<div id="{cat}" class="news-section" style="display:none"><div class="news-grid">' + 
                "".join([f'<div class="card"><a href="{i["link"]}" target="_blank">{i["title"]}</a><div class="meta"><span class="source-tag">{i["source"]}</span><span>{i["published"][:16] if i["published"] else ""}</span></div></div>' for i in items]) + 
                '</div></div>' for cat, items in news_data.items()]) }
        </div>

        <script>
            function toggleTheme() {{
                const body = document.body;
                const isDark = body.getAttribute('data-theme') === 'dark';
                body.setAttribute('data-theme', isDark ? 'light' : 'dark');
                localStorage.setItem('theme', isDark ? 'light' : 'dark');
            }}

            function toggleLang() {{
                const html = document.getElementById('html-tag');
                const isHeb = html.getAttribute('dir') === 'rtl';
                html.setAttribute('dir', isHeb ? 'ltr' : 'rtl');
                html.setAttribute('lang', isHeb ? 'en' : 'he');
                document.getElementById('main-title').innerHTML = isHeb ? '<i class="fas fa-globe"></i> Ohad Baram News Dashboard' : '<i class="fas fa-globe"></i> לוח החדשות של אוהד ברעם';
            }}

            function showCategory(id) {{
                document.querySelectorAll('.news-section').forEach(s => s.style.display = 'none');
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(id).style.display = 'block';
                event.currentTarget.classList.add('active');
            }}

            // Init
            document.querySelector('.tab-btn').click();
            if(localStorage.getItem('theme')) document.body.setAttribute('data-theme', localStorage.getItem('theme'));
        </script>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

if __name__ == '__main__':
    news = fetch_news()
    update_dashboard(news)
    print("Dashboard fully updated!")
