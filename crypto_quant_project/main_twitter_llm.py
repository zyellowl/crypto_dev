import time
import configparser
import os
from core.resource_fetcher import ResourceFetcher
from core.llm_analyzer import LLMAnalyzer

def aggregate_twitter_content(resource_fetcher, twitter_users, rsshub_url=None, max_items=20):
    tweets = resource_fetcher.fetch_nitter_rss(twitter_users)
    all_texts = [item['text'] for item in tweets]
    if rsshub_url:
        rsshub_tweets = resource_fetcher.fetch_rsshub_twitter(rsshub_url, max_items=max_items)
        all_texts.extend([f"{t['title']} {t['summary']}" for t in rsshub_tweets])
    # 去重和去空
    all_texts = [t.strip() for t in all_texts if t and t.strip()]
    return all_texts

def generate_signal_from_llm(llm_analyzer, texts, symbol):
    """
    组装推文内容为prompt，调用LLM分析，输出买入/卖出/观望
    """
    if not texts:
        print("No twitter content found.")
        return 'HOLD'
    prompt = f"请根据以下所有推特内容，判断对{symbol}的操作建议（买入/卖出/观望），并简要说明理由：\n" + "\n".join(texts)
    print(f"\n[LLM Prompt Preview]\n{prompt[:300]}...\n")
    analysis = llm_analyzer.analyze_text(prompt)
    if not analysis or 'sentiment_score' not in analysis:
        print("LLM未返回有效分析，建议观望。")
        return 'HOLD'
    score = analysis['sentiment_score']
    print(f"LLM情绪分: {score:.2f}，置信度: {analysis.get('confidence', 0):.2f}")
    if score > 0.2:
        return 'BUY'
    elif score < -0.2:
        return 'SELL'
    else:
        return 'HOLD'

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    twitter_users = config.get('Nitter', 'TWITTER_USERNAMES').split(',')
    rsshub_url = "http://localhost:1200/twitter/home_latest"
    symbol = config.get('Trading', 'SYMBOLS').split(',')[0]

    resource_fetcher = ResourceFetcher(config_file=config_path)
    llm_analyzer = LLMAnalyzer(config_file=config_path)

    print(f"抓取推特内容并分析 {symbol} 的操作建议...")
    texts = aggregate_twitter_content(resource_fetcher, twitter_users, rsshub_url=rsshub_url, max_items=20)
    print(f"共聚合 {len(texts)} 条推文内容。")
    signal = generate_signal_from_llm(llm_analyzer, texts, symbol)
    print(f"\n【最终建议】{symbol}: {signal}")

if __name__ == '__main__':
    main() 