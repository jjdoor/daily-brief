import os
import requests
from datetime import datetime, timezone, timedelta

SEARCH_QUERIES = [
    'AI tools 2026',
    'indie hacker revenue',
    'side income programmer',
    'AI startup launch',
    'build in public revenue',
]

def fetch_youtube_videos(min_views=5000, max_age_hours=26):
    api_key = os.environ.get('YOUTUBE_API_KEY', '')
    if not api_key:
        print('YOUTUBE_API_KEY not set, skipping')
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    items = []
    seen = set()

    for query in SEARCH_QUERIES:
        try:
            # 搜索视频
            search_resp = requests.get(
                'https://www.googleapis.com/youtube/v3/search',
                params={
                    'part': 'snippet',
                    'q': query,
                    'type': 'video',
                    'order': 'viewCount',
                    'publishedAfter': cutoff,
                    'maxResults': 5,
                    'key': api_key,
                },
                timeout=10,
            )
            search_data = search_resp.json()
            video_ids = [i['id']['videoId'] for i in search_data.get('items', []) if 'videoId' in i.get('id', {})]

            if not video_ids:
                continue

            # 拉取播放量
            stats_resp = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                params={
                    'part': 'statistics,snippet',
                    'id': ','.join(video_ids),
                    'key': api_key,
                },
                timeout=10,
            )
            for video in stats_resp.json().get('items', []):
                vid = video['id']
                if vid in seen:
                    continue
                view_count = int(video['statistics'].get('viewCount', 0))
                if view_count < min_views:
                    continue
                seen.add(vid)
                items.append({
                    'source': 'YouTube',
                    'title': video['snippet']['title'],
                    'channel': video['snippet']['channelTitle'],
                    'views': view_count,
                    'url': f'https://www.youtube.com/watch?v={vid}',
                    'summary': f"频道：{video['snippet']['channelTitle']} | 播放量：{view_count:,}",
                })
        except Exception as e:
            print(f'YouTube fetch failed for query={query!r}: {e}')

    items.sort(key=lambda x: x['views'], reverse=True)
    return items[:8]
