import requests
import feedparser
from datetime import datetime

RSS_FEEDS = [
    'https://news.ycombinator.com/rss',
    'https://www.reddit.com/.rss',
    # Add more RSS feeds as needed
]

def fetch_news():
    news_items = []
    for feed in RSS_FEEDS:
        response = requests.get(feed)
        if response.status_code == 200:
            feed_data = feedparser.parse(response.content)
            for entry in feed_data.entries:
                news_items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                })
    return news_items

def update_dashboard(news_items):
    with open('dashboard.html', 'w') as file:
        file.write('<html><body><h1>Latest News</h1><ul>\n')
        for item in news_items:
            file.write(f'<li><a href="{item["link"]}">{item["title"]}</a> - {item["published"]}</li>\n')
        file.write('</ul></body></html>')

if __name__ == '__main__':
    latest_news = fetch_news()
    update_dashboard(latest_news)
    print(f'Dashboard updated with {len(latest_news)} news items on {datetime.utcnow()}')
