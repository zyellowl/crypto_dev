#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_tweets.py

可执行脚本：使用 undetected_chromedriver 绕过 Cloudflare，抓取 lightbrd.com 上的推文；结果保存为 CSV。

依赖：
  pip install undetected-chromedriver beautifulsoup4 pandas
"""
import argparse
import csv
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc


def parse_args():
    parser = argparse.ArgumentParser(description="抓取 lightbrd.com 搜索推文并导出 CSV")
    parser.add_argument("-q", "--query", required=True, help="搜索关键词 (e.g. acconebtc)")
    parser.add_argument("-n", "--scrolls", type=int, default=5, help="下拉加载次数, 默认 5")
    parser.add_argument("-o", "--output", default="tweets.csv", help="输出 CSV 文件名")
    parser.add_argument("--headless", action="store_true", help="是否以无头模式运行浏览器")
    return parser.parse_args()


def init_driver(headless: bool = False):
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options)
    return driver


def fetch_tweets_via_selenium(query: str, scrolls: int, delay: float, headless: bool):
    driver = init_driver(headless=headless)
    try:
        url = f"https://lightbrd.com/search?f=tweets&q={query}"
        driver.get(url)
        time.sleep(delay)
        for _ in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(delay)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    tweets = []
    # 根据页面结构提取推文元素
    for card in soup.select('div[class*="tweetCard"], article'):  # 支持多种可能结构
        user_el = card.select_one('a[href*="twitter.com"]')
        text_el = card.select_one('div[class*="textContent"]') or card.select_one('p')
        time_el = card.select_one('time')
        user = user_el.get_text(strip=True) if user_el else None
        text = text_el.get_text(strip=True) if text_el else None
        created_at = None
        if time_el:
            created_at = time_el.get('datetime') or time_el.get_text(strip=True)
        if text:
            tweets.append({'created_at': created_at, 'user': user, 'text': text})
    return tweets


def save_to_csv(data, output_file):
    keys = ['created_at', 'user', 'text']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"已保存 {len(data)} 条推文至 {output_file}")


def main():
    args = parse_args()
    print("开始使用 Selenium 绕过 Cloudflare 抓取推文...")
    tweets = fetch_tweets_via_selenium(args.query, scrolls=args.scrolls, delay=2.0, headless=args.headless)
    print(f"共抓取到 {len(tweets)} 条推文。")
    save_to_csv(tweets, args.output)


if __name__ == '__main__':
    main()
