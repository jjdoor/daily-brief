import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from google import genai

sys.path.insert(0, os.path.dirname(__file__))
from fetch_github import fetch_github_trending
from fetch_sources import fetch_rss_feeds


def build_prompt(github_repos, rss_items):
    github_text = '\n'.join([
        f"- [{r['name']}]({r['url']}): {r['description']} | 今日新增: {r['stars_today']} | 语言: {r['language']}"
        for r in github_repos[:30]
    ]) or '（无数据）'

    rss_text = '\n'.join([
        f"- [{item['source']}] {item['title']}\n  摘要: {item['summary'][:200]}\n  链接: {item['url']}"
        for item in rss_items[:50]
    ]) or '（无数据）'

    return f"""你是一名技术简报编辑，读者是关注 AI/ML 工具和独立开发者动态的中文开发者。

【过滤规则——满足以下任一条则丢弃】
1. 纯广告、招聘、自我营销
2. 没有具体技术信息的泛泛而谈
3. 与 AI/ML 或独立开发完全无关
4. 同一工具/事件重复报道（只保留信息量最大的一条）

【保留优先级】
- 新发布的 AI/ML 工具、模型、论文、开源项目
- 独立开发者构建产品的实战经验、增长策略、收入案例
- 重要的开源项目更新
- 值得关注的技术趋势讨论

【输出格式——严格遵守，每个板块都必须输出】

## 🔥 GitHub 今日亮点

精选 5 个最值得关注的仓库：
**仓库名** | 今日 +N stars
一句话（≤25字）：解决什么问题，谁应该关注
🔗 https://github.com/xxx

---

## 💡 独立开发者动态

精选 5 条独立开发者相关内容（产品发布、增长经验、工具推荐）：
**[来源]** 标题
核心内容（≤40字）
🔗 链接

---

## 🤖 AI/ML 技术动态

精选 5 条 AI/ML 领域最新动态：
**[来源]** 标题
核心内容（≤40字）
🔗 链接

---

## 📈 今日脉搏

2-3 句话总结今天的整体技术方向和值得重点关注的趋势。

---

⚠️ 重要：严格基于我提供的原始数据，禁止编造任何链接、仓库名或数据。

=== GitHub Trending 原始数据 ===
{github_text}

=== 今日资讯原始数据 ===
{rss_text}
"""


def send_email(subject, content, to_email, gmail_user, gmail_password):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [to_email], msg.as_string())

    print(f'Email sent to {to_email}')


def main():
    print('Fetching GitHub Trending...')
    github_repos = fetch_github_trending()
    print(f'  Got {len(github_repos)} repos')

    print('Fetching RSS feeds...')
    rss_items = fetch_rss_feeds()
    print(f'  Got {len(rss_items)} items')

    print('Generating brief with Gemini...')
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    prompt = build_prompt(github_repos, rss_items)

    import time
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            brief = response.text
            break
        except Exception as e:
            if '429' in str(e) and attempt < 3:
                wait = 30 * (attempt + 1)
                print(f'Rate limited, retrying in {wait}s...')
                time.sleep(wait)
            else:
                raise

    today = datetime.now().strftime('%Y-%m-%d %A')
    subject = f'🤖 AI & 独立开发日报 {today}'

    print('Sending email...')
    send_email(
        subject=subject,
        content=brief,
        to_email=os.environ['TO_EMAIL'],
        gmail_user=os.environ['GMAIL_USER'],
        gmail_password=os.environ['GMAIL_APP_PASSWORD'],
    )

    print('Done!')
    print('\n--- Brief Preview (first 800 chars) ---')
    print(brief[:800])


if __name__ == '__main__':
    main()
