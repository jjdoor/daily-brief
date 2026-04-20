import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from groq import Groq

sys.path.insert(0, os.path.dirname(__file__))
from fetch_github import fetch_github_trending
from fetch_sources import fetch_rss_feeds
from fetch_youtube import fetch_youtube_videos


def build_prompt(github_repos, rss_items, youtube_items):
    github_text = '\n'.join([
        f"- [{r['name']}]({r['url']}): {r['description']} | 今日新增: {r['stars_today']} | 语言: {r['language']}"
        for r in github_repos[:30]
    ]) or '（无数据）'

    rss_text = '\n'.join([
        f"- [{item['source']}] {item['title']}\n  摘要: {item['summary'][:200]}\n  链接: {item['url']}"
        for item in rss_items[:60]
    ]) or '（无数据）'

    youtube_text = '\n'.join([
        f"- {item['title']} | 播放量: {item['views']:,} | 频道: {item['channel']}\n  链接: {item['url']}"
        for item in youtube_items
    ]) or '（无数据）'

    return f"""你是一名副业情报编辑，读者是一名有编程能力、正在探索副业收入的中文程序员，他关注 AI 工具机会和独立开发者变现案例。

【读者核心问题】
1. 今天有哪些 AI 工具值得立刻去试？
2. 别人用什么方法赚到了钱？我能复制吗？
3. 有哪些新的技术需求或市场信号？

【过滤规则——满足以下任一条则丢弃】
1. 纯广告、招聘、学术论文（无实用价值）
2. 没有具体信息的泛泛而谈
3. 与 AI 工具、副业变现、程序员接单完全无关
4. 同一事件重复报道（只保留信息量最大的一条）

【输出格式——严格遵守，每个板块都必须输出】

## 🛠 今日 AI 工具情报

精选 5 个值得关注的 AI 新工具或重大更新：
**工具名**
一句话（≤30字）：能做什么、解决什么问题、对程序员副业有何用
🔗 链接

---

## 💰 副业变现案例

精选 5 条独立开发者赚钱案例或市场需求信号：
**[来源]** 标题
核心信息（≤40字）：谁、用什么方法、赚了多少或发现了什么需求
🔗 链接

---

## 📺 YouTube 热度信号

精选 3 个播放量高的近期视频（播放量高 = 话题有热度 = 市场在关注）：
**标题** | 播放量：N 万
一句话：这个话题火说明什么机会
🔗 链接

---

## ⚡ 今日机会判断

2-3 句话直接告诉读者：今天最值得关注的副业机会方向是什么，为什么。

---

⚠️ 重要：严格基于我提供的原始数据，禁止编造任何链接、数据或案例。

=== GitHub Trending 原始数据 ===
{github_text}

=== RSS 资讯原始数据 ===
{rss_text}

=== YouTube 热门视频原始数据 ===
{youtube_text}
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

    print('Fetching YouTube videos...')
    youtube_items = fetch_youtube_videos()
    print(f'  Got {len(youtube_items)} videos')

    print('Generating brief with Groq...')
    client = Groq(api_key=os.environ['GROQ_API_KEY'])
    prompt = build_prompt(github_repos, rss_items, youtube_items)
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2048,
    )
    brief = response.choices[0].message.content

    today = datetime.now().strftime('%Y-%m-%d %A')
    subject = f'💰 副业情报日报 {today}'

    print('Sending email...')
    send_email(
        subject=subject,
        content=brief,
        to_email=os.environ['TO_EMAIL'],
        gmail_user=os.environ['GMAIL_USER'],
        gmail_password=os.environ['GMAIL_APP_PASSWORD'],
    )

    print('Done!')
    print('\n--- Brief Preview ---')
    print(brief[:800])


if __name__ == '__main__':
    main()
