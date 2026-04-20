import requests
from bs4 import BeautifulSoup


def fetch_github_trending(since='daily'):
    languages = ['python', 'jupyter-notebook', '']
    repos = []
    seen = set()

    for lang in languages:
        url = f'https://github.com/trending/{lang}?since={since}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('article.Box-row'):
                name_tag = article.select_one('h2 a')
                desc_tag = article.select_one('p')
                stars_tag = article.select_one('span.d-inline-block.float-sm-right')
                lang_tag = article.select_one('span[itemprop="programmingLanguage"]')

                if not name_tag:
                    continue

                repo_path = name_tag.get('href', '').strip('/')
                if repo_path in seen:
                    continue
                seen.add(repo_path)

                repos.append({
                    'name': repo_path,
                    'url': 'https://github.com/' + repo_path,
                    'description': desc_tag.get_text(strip=True) if desc_tag else '',
                    'stars_today': stars_tag.get_text(strip=True).replace('\n', '').strip() if stars_tag else '',
                    'language': lang_tag.get_text(strip=True) if lang_tag else '',
                })
        except Exception as e:
            print(f'GitHub Trending fetch failed for lang={lang!r}: {e}')

    return repos
