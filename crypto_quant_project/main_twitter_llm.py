import time
import configparser
import os
import json
from datetime import datetime
from core.resource_fetcher import ResourceFetcher
from core.llm_analyzer import LLMAnalyzer

def load_tweet_log(log_path):
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_tweet_log(log_path, tweet_ids):
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(list(tweet_ids), f, ensure_ascii=False, indent=2)

def get_tweet_id(item):
    # 优先用url，否则用内容hash
    if 'url' in item and item['url']:
        return item['url']
    return str(hash(item.get('text', '')))

def aggregate_twitter_content(resource_fetcher, vip_users, rsshub_url=None, max_items=20, tweet_log=None, new_tweet_ids=None):
    all_texts = []
    new_tweets_found = False
    # 聚合VIP用户内容（每人只取5条）
    if vip_users:
        print("\n=== VIP用户推文 ===")
        for user in vip_users:
            print(f"\n>> 抓取VIP用户 @{user} 最新5条推文...")
            tweets = resource_fetcher.fetch_nitter_rss([user])
            user_new = False
            for item in tweets[:5]:
                tweet_id = get_tweet_id(item)
                tweet_text = f"[VIP][{user}] {item['text']}"
                pub_time = item.get('published', '')
                if tweet_log is not None and tweet_id in tweet_log:
                    print(f"[{pub_time}] (已处理) {tweet_text[:200]}...")
                else:
                    print(f"[{pub_time}] (新) {tweet_text[:200]}...")
                    all_texts.append(tweet_text)
                    if new_tweet_ids is not None:
                        new_tweet_ids.add(tweet_id)
                    user_new = True
            if not user_new:
                print(f"[INFO] 用户@{user}无新推文。")
    
    if rsshub_url:
        print("\n=== RSSHub推文 ===")
        rsshub_tweets = resource_fetcher.fetch_rsshub_twitter(rsshub_url, max_items=max_items)
        rsshub_new = False
        for t in rsshub_tweets:
            tweet_id = t.get('url') or str(hash(t.get('title', '') + t.get('summary', '')))
            tweet_text = f"{t['title']} {t['summary']}"
            pub_time = t.get('published', '')
            if tweet_log is not None and tweet_id in tweet_log:
                print(f"[{pub_time}] (已处理) {tweet_text[:200]}...")
            else:
                print(f"[{pub_time}] (新) {tweet_text[:200]}...")
                all_texts.append(tweet_text)
                if new_tweet_ids is not None:
                    new_tweet_ids.add(tweet_id)
                rsshub_new = True
        if not rsshub_new:
            print(f"[INFO] RSSHub无新推文。")
    # 去重和去空
    all_texts = [t.strip() for t in all_texts if t and t.strip()]
    return all_texts

def generate_signal_from_llm(llm_analyzer, texts, symbols):
    """
    组装推文内容为prompt，调用LLM分析，输出每个币种的买入/卖出/观望建议
    """
    if not texts:
        print("无新推文，无需分析。")
        return {s: 'HOLD' for s in symbols}
    
    # 为所有币种统一分析
    symbols_str = ", ".join(symbols)
    prompt = f"""请根据以下所有推特内容，分别判断对这些币种的操作建议：{symbols_str}
要求：
1. 分析每个币种相关的市场情绪
2. 给出每个币种的操作建议（买入/卖出/观望）
3. 简要说明理由

推文内容：
""" + "\n".join(texts)
    
    print(f"\n[LLM Prompt Preview]\n{prompt[:500]}...\n")
    analysis = llm_analyzer.analyze_text(prompt)
    
    if not analysis or 'sentiment_score' not in analysis:
        print("LLM未返回有效分析，建议全部观望。")
        return {s: 'HOLD' for s in symbols}
    
    # 使用统一的情绪分数
    score = analysis['sentiment_score']
    confidence = analysis.get('confidence', 0)
    print(f"整体市场情绪分: {score:.2f}，置信度: {confidence:.2f}")
    
    # 根据情绪分数生成信号
    signals = {}
    for symbol in symbols:
        if score > 0.2:
            signals[symbol] = 'BUY'
        elif score < -0.2:
            signals[symbol] = 'SELL'
        else:
            signals[symbol] = 'HOLD'
    
    return signals

def main_once(tweet_log_path, tweet_log):
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    vip_users = config.get('Users', 'VIP_USERS', fallback='').split(',')
    vip_users = [u.strip() for u in vip_users if u.strip()]
    rsshub_url = "http://localhost:1200/twitter/home_latest"
    symbols = [s.split('/')[0].upper() for s in config.get('Trading', 'SYMBOLS').split(',')]

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始新一轮分析...")
    print(f"关注币种: {', '.join(symbols)}")
    print(f"VIP用户: {', '.join(vip_users)}")

    resource_fetcher = ResourceFetcher(config_file=config_path)
    llm_analyzer = LLMAnalyzer(config_file=config_path)

    new_tweet_ids = set()
    texts = aggregate_twitter_content(resource_fetcher, vip_users, rsshub_url=rsshub_url, max_items=20, tweet_log=tweet_log, new_tweet_ids=new_tweet_ids)
    print(f"\n共聚合 {len(texts)} 条新推文内容，开始LLM分析...")
    signals = generate_signal_from_llm(llm_analyzer, texts, symbols)
    print("\n=== 最终建议 ===")
    for symbol, signal in signals.items():
        print(f"【{symbol}】: {signal}")
    # 持久化新推文ID
    if new_tweet_ids:
        tweet_log.update(new_tweet_ids)
        save_tweet_log(tweet_log_path, tweet_log)

def main_loop():
    interval = 60  # 1分钟
    tweet_log_path = os.path.join(os.path.dirname(__file__), 'tweet_log.json')
    tweet_log = load_tweet_log(tweet_log_path)
    print(f"定时任务启动，每{interval//60}分钟自动执行一次推特聚合与LLM分析。按Ctrl+C退出。")
    try:
        while True:
            print("\n" + "="*50)
            main_once(tweet_log_path, tweet_log)
            print(f"\n等待{interval//60}分钟后开始下一轮...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n已手动终止定时任务。")

if __name__ == '__main__':
    main_loop() 