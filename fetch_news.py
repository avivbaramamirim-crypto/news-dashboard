import requests
import feedparser
from datetime import datetime

# הגדרת מקורות החדשות לפי קטגוריות
RSS_FEEDS = {
    'ישראל': [
        {'name': 'Google News Israel', 'url': 'https://news.google.com/rss/search?q=israel&hl=he&gl=IL&ceid=IL:he'},
        {'name': 'ynet', 'url': 'https://www.ynet.co.il/Integration/StoryRss2.xml'}
    ],
    'בינה מלאכותית': [
        {'name': 'AI News', 'url': 'https://www.artificialintelligence-news.com/feed/'},
        {'name': 'Hacker News (AI)', 'url': 'https://news.ycombinator.com/rss'}
    ],
    'טכנולוגיה': [
        {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml'},
        {'name': 'Wired', 'url': 'https://www.wired.com/feed/rss'}
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
                    for entry in feed_data.entries[:8]: # 8 ידיעות מכל מקור
                        categorized_news[category].append({
                            'source': feed['name'],
                            'title': entry.title,
                            'link': entry.link,
                            'published': entry.get('published', 'No Date')
                        })
            except Exception as e:
                print(f"Error fetching {feed['name']}: {e}")
    return categorized_news

def update_dashboard(news_data):
    filename = 'israel-ai-dashboard.html'
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>לוח החדשות של אוהד ברעם</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {{
                --bg: #0f172a; --card-bg: #1e293b; --accent: #38bdf8;
                --text: #f8fafc; --text-dim: #94a3b8;
            }}
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; line-height: 1.6; }}
            .header {{ background: linear-gradient(135deg, #0ea5e9, #2563eb); padding: 40px 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; }}
            .update-tag {{ font-size: 0.9rem; opacity: 0.8; margin-top: 10px; display: block; }}
            
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin-top: -25px; position: sticky; top: 0; z-index: 100; padding: 10px; }}
            .tab-btn {{ background: var(--card-bg); border: none; color: var(--text); padding: 12px 25px; border-radius: 50px; cursor: pointer; font-weight: bold; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
            .tab-btn.active {{ background: var(--accent); color: #000; transform: translateY(-2px); }}

            .container {{ max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .category-content {{ display: none; }}
            .category-content.active {{ display: block; animation: fadeIn 0.5s; }}

            .card {{ background: var(--card-bg); border-radius: 16px; padding: 20px; transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; justify-content: space-between; }}
            .card:hover {{ transform: translateY(-5px); border-color: var(--accent); box-shadow: 0 10px 30px rgba(56, 189, 248, 0.1); }}
            .card a {{ color: var(--text); text-decoration: none; font-size: 1.1rem; font-weight: 600; display: block; margin-bottom: 10px; }}
            .card .source {{ font-size: 0.75rem; background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 4px 10px; border-radius: 6px; display: inline-block; }}
            .card .date {{ font-size: 0.75rem; color: var(--text-dim); margin-top: 10px; }}
            
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            @media (max-width: 600px) {{ h1 {{ font-size: 1.8rem; }} .tabs {{ flex-wrap: wrap; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1><i class="fas fa-newspaper"></i> לוח החדשות של אוהד ברעם</h1>
            <span class="update-tag">עדכון אחרון: {now}</span>
        </div>

        <div class="tabs">
            {" ".join([f'<button class="tab-btn" onclick="showCategory(\'{cat}\')" id="btn-{cat}">{cat}</button>' for cat in news_data.keys()])}
        </div>

        <div class="container">
    """
    
    first = True
    for category, items in news_data.items():
        active_class = "active" if first else ""
        html_template += f'<div id="{category}" class="category-content {active_class}"><div class="news-grid">'
        for item in items:
            html_template += f"""
                <div class="card">
                    <a href="{item['link']}" target="_blank">{item['title']}</a>
                    <div>
                        <span class="source">{item['source']}</span>
                        <div class="date">{item['published']}</div>
                    </div>
                </div>
            """
        html_template += '</div></div>'
        first = False

    html_template += """
        </div>
        <script>
            function showCategory(catId) {
                document.querySelectorAll('.category-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(catId).classList.add('active');
                event.currentTarget.classList.add('active');
            }
            // Set first tab as active on load
            document.querySelector('.tab-btn').classList.add('active');
        </script>
    </body>
    </html>
    """
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

if __name__ == '__main__':
    news = fetch_news()
    update_dashboard(news)
    print("Dashboard Updated Successfully!")
