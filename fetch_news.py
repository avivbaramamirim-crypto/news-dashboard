import requests
import feedparser
from datetime import datetime

# רשימת מקורות חדשות רלוונטיים (AI וישראל)
RSS_FEEDS = [
    {'name': 'Hacker News (AI)', 'url': 'https://news.ycombinator.com/rss'},
    {'name': 'Google News Israel', 'url': 'https://news.google.com/rss/search?q=israel&hl=he&gl=IL&ceid=IL:he'},
    {'name': 'AI News', 'url': 'https://www.artificialintelligence-news.com/feed/'},
    {'name': 'The Verge (Tech)', 'url': 'https://www.theverge.com/rss/index.xml'}
]

def fetch_news():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0'} # מונע חסימות מחלק מהאתרים
    for feed in RSS_FEEDS:
        try:
            response = requests.get(feed['url'], headers=headers, timeout=10)
            if response.status_code == 200:
                feed_data = feedparser.parse(response.content)
                # לוקח רק את 10 הידיעות האחרונות מכל מקור
                for entry in feed_data.entries[:10]:
                    published = entry.get('published', entry.get('updated', 'No Date'))
                    news_items.append({
                        'source': feed['name'],
                        'title': entry.title,
                        'link': entry.link,
                        'published': published
                    })
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")
    return news_items

def update_dashboard(news_items):
    # שים לב: שיניתי את שם הקובץ שיתאים למה שיש לך ב-GitHub
    filename = 'israel-ai-dashboard.html'
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>לוח החדשות של אוהד ברעם</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ color: #00ffcc; text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .last-updated {{ text-align: center; color: #888; font-size: 0.9em; margin-bottom: 30px; }}
            .news-card {{ background: #2d2d2d; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s; }}
            .news-card:hover {{ transform: scale(1.01); background: #363636; }}
            .news-card a {{ color: #00ffcc; text-decoration: none; font-size: 1.2em; font-weight: bold; }}
            .news-card .meta {{ font-size: 0.8em; color: #aaa; margin-top: 8px; }}
            .source-tag {{ background: #444; color: #fff; padding: 2px 8px; border-radius: 4px; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>לוח החדשות המותאם של אוהד ברעם</h1>
            <p class="last-updated">עודכן לאחרונה: {datetime.now().strftime('%H:%M:%D')}</p>
            <div id="news-list">
    """
    
    for item in news_items:
        html_content += f"""
            <div class="news-card">
                <a href="{item['link']}" target="_blank">{item['title']}</a>
                <div class="meta">
                    <span class="source-tag">{item['source']}</span>
                    <span>{item['published']}</span>
                </div>
            </div>
        """
        
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

if __name__ == '__main__':
    print("Fetching news...")
    latest_news = fetch_news()
    update_dashboard(latest_news)
    print(f'Dashboard updated with {len(latest_news)} items.')
