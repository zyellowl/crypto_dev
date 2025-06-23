import requests
import configparser
import praw
import feedparser
from rsshub_twitter_fetcher import RssHubTwitterFetcher

class ResourceFetcher:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # NewsAPI configuration
        if 'API' in self.config and 'NEWS_API_KEY' in self.config['API']:
            self.news_api_key = self.config['API']['NEWS_API_KEY']
        else:
            self.news_api_key = None
        self.news_base_url = 'https://newsapi.org/v2/everything'

        # Reddit client
        if 'Reddit' in self.config and self.config['Reddit'].get('REDDIT_CLIENT_ID'):
            try:
                self.reddit_client = praw.Reddit(
                    client_id=self.config['Reddit']['REDDIT_CLIENT_ID'],
                    client_secret=self.config['Reddit']['REDDIT_CLIENT_SECRET'],
                    user_agent=self.config['Reddit']['REDDIT_USER_AGENT']
                )
            except Exception as e:
                print(f"Warning: Could not initialize Reddit client: {e}")
                self.reddit_client = None
        else:
            self.reddit_client = None

    def fetch_news(self, keywords, language='en', sort_by='publishedAt', page_size=20):
        """Fetches news articles from NewsAPI."""
        if not self.news_api_key or self.news_api_key == 'YOUR_NEWS_API_KEY':
            print("Warning: NEWS_API_KEY not found or is a placeholder. Skipping news fetch.")
            return []

        params = {'q': keywords, 'apiKey': self.news_api_key, 'language': language, 'sortBy': sort_by, 'pageSize': page_size}
        try:
            response = requests.get(self.news_base_url, params=params)
            response.raise_for_status()
            return response.json().get('articles', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []

    def fetch_nitter_rss(self, usernames):
        """Fetches tweets for a list of usernames using a Nitter RSS feed (deprecated, kept for compatibility)."""
        all_tweets = []
        for username in usernames:
            if not username.strip():
                continue
            # 推荐直接用RSSHub
            print(f"[WARN] fetch_nitter_rss建议用RSSHub替代。当前username: {username}")
            # 可选：兼容老接口，直接用RSSHub
            rsshub_url = f"http://localhost:1200/twitter/user/{username}"
            fetcher = RssHubTwitterFetcher(rsshub_url)
            tweets = fetcher.fetch()
            for t in tweets:
                all_tweets.append({
                    'source': f'RSSHub (@{username})',
                    'text': f"{t['title']} {t['summary']}",
                    'url': t['url']
                })
        return all_tweets

    def fetch_reddit_posts(self, subreddits, limit=5):
        """Fetches recent posts from a list of subreddits."""
        if not self.reddit_client:
            print("Warning: Reddit client not configured. Skipping Reddit fetch.")
            return []
            
        all_posts = []
        for sub_name in subreddits:
            try:
                print(f"Fetching posts from r/{sub_name}...")
                subreddit = self.reddit_client.subreddit(sub_name)
                for post in subreddit.new(limit=limit):
                    all_posts.append({
                        'source': f'Reddit (r/{sub_name})',
                        'text': f"{post.title} - {post.selftext}"[:250], # Truncate long posts
                        'url': post.url
                    })
            except Exception as e:
                print(f"Error fetching from subreddit r/{sub_name}: {e}")
        return all_posts

    def fetch_rsshub_twitter(self, rsshub_url, max_items=None):
        """通过RSSHub地址抓取推文内容"""
        fetcher = RssHubTwitterFetcher(rsshub_url)
        return fetcher.fetch(max_items=max_items)

if __name__ == '__main__':
    # Example Usage
    import os
    config_path = '../config.ini'
    if not os.path.exists(config_path):
        print("Cannot run example without a config file.")
    else:
        fetcher = ResourceFetcher(config_file=config_path)

        # 1. Fetch news (if configured)
        print("\n--- Fetching News ---")
        news_articles = fetcher.fetch_news('bitcoin', page_size=2)
        if news_articles:
            print(f"Fetched {len(news_articles)} news articles.")
            print(news_articles[0])

        # 2. Fetch Tweets via Nitter RSS
        print("\n--- Fetching Tweets via Nitter RSS ---")
        twitter_usernames = fetcher.config.get('Nitter', 'TWITTER_USERNAMES', fallback='').split(',')
        if twitter_usernames and twitter_usernames[0]:
            tweets = fetcher.fetch_nitter_rss(twitter_usernames)
            if tweets:
                print(f"Fetched {len(tweets)} tweets.")
                print(tweets[0])
        else:
            print("No Twitter usernames configured in config.ini under [Nitter].")

        # 3. Fetch Reddit posts (if configured)
        print("\n--- Fetching Reddit Posts ---")
        subreddits = fetcher.config.get('Trading', 'REDDIT_SUBREDDITS', fallback='').split(',')
        if subreddits and subreddits[0] and fetcher.reddit_client:
            posts = fetcher.fetch_reddit_posts(subreddits, limit=1)
            if posts:
                print(f"Fetched {len(posts)} Reddit posts.")
                print(posts[0])
        else:
            print("Reddit client not configured or no subreddits specified.")
