import feedparser
from datetime import datetime, timezone, timedelta


RSS_FEEDS = [
    # AI 工具更新
    ('TLDR AI',          'https://tldr.tech/api/rss/ai'),
    ('AI News',          'https://buttondown.com/ainews/rss'),
    ('Product Hunt',     'https://www.producthunt.com/feed'),
    ('HN 首页',          'https://hnrss.org/frontpage'),
    ('Reddit LocalLLaMA','https://www.reddit.com/r/LocalLLaMA/.rss'),
    # 副业 / 变现案例
    ('Indie Hackers',    'https://www.indiehackers.com/feed.rss'),
    ('HN Show HN',       'https://hnrss.org/show'),
    ('Reddit SideProject','https://www.reddit.com/r/SideProject/.rss'),
    ('Reddit Freelance', 'https://www.reddit.com/r/freelance/.rss'),
    # 技术机会信号
    ('Reddit MachineLearning', 'https://www.reddit.com/r/MachineLearning/.rss'),
    ('The Batch',        'https://www.deeplearning.ai/the-batch/feed/'),
]


def fetch_rss_feeds(max_age_hours=26):
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                if published and published < cutoff:
                    continue

                summary = entry.get('summary', '') or ''
                items.append({
                    'source': source_name,
                    'title': entry.get('title', ''),
                    'summary': summary[:300],
                    'url': entry.get('link', ''),
                    'published': published.isoformat() if published else '',
                })
        except Exception as e:
            print(f'RSS fetch failed for {source_name}: {e}')

    return items
