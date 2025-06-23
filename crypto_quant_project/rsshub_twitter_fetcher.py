import random
import sys
import feedparser

class RssHubTwitterFetcher:
    """
    用于解析RSSHub的Twitter Home/用户/搜索等RSS内容。
    """
    def __init__(self, rss_url):
        self.rss_url = rss_url

    def fetch(self, max_items=None):
        """
        解析RSS内容，返回推文列表。
        :param max_items: 限制返回条数，None为全部
        :return: List[dict]
        """
        print(f"[INFO] 解析RSSHub: {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        if feed.bozo:
            print(f"[ERROR] RSS解析失败: {feed.bozo_exception}")
            return []
        tweets = []
        entries = feed.entries if max_items is None else feed.entries[:max_items]
        for entry in entries:
            tweets.append({
                "title": entry.title,
                "summary": getattr(entry, "summary", ""),
                "url": entry.link,
                "published": getattr(entry, "published", "")
            })
        return tweets

if __name__ == "__main__":
    # 示例：解析本地RSSHub
    RSSHUB_URL = "http://localhost:1200/twitter/home_latest"
    fetcher = RssHubTwitterFetcher(RSSHUB_URL)
    tweets = fetcher.fetch()
    if tweets:
        print(f"Latest tweets from RSSHub home_latest:")
        for t in tweets:
            print(f"[{t['published']}] {t['title']}\n  {t['url']}\n  {t['summary']}\n")
    else:
        print("No tweets found or failed to fetch.") 